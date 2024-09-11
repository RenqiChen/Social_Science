# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
from functools import partial

from prompt import Prompts
from werewolf_utils import (
    check_winning,
    update_alive_players,
    majority_vote,
    extract_name_and_id,
    extract_scientist_names,
    team_description,
    n2s,
    set_parsers,
)
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline
import agentscope
from agentscope.rag import KnowledgeBank


# pylint: disable=too-many-statements
def main() -> None:
    """werewolf game"""
    # default settings
    HostMsg = partial(Msg, name="Moderator", role="assistant", echo=True)
    healing, poison = True, True
    MAX_WEREWOLF_DISCUSSION_ROUND = 3
    MAX_GAME_ROUND = 6
    # read model and agent configs, and initialize agents automatically
    survivors = agentscope.init(
        model_configs="./configs/model_configs.json",
        agent_configs="./configs/agent_configs.json",
        project="Scientist",
    )
    # the knowledge bank can be configured by loading config file
    knowledge_bank = KnowledgeBank(configs="configs/knowledge_config.json")

    # alternatively, we can easily input the configs to add data to RAG
    knowledge_bank.add_data_as_knowledge(
        knowledge_id="author_information",
        emb_model_name="ollama_embedding-qwen:0.5b",
        data_dirs_and_types={
            "../../docs/sphinx_doc/en/source/tutorial": [".md"],
        },
    )
    roles = ["Scientist1", "Scientist2", "Scientist3"]
    scientists = survivors
    # let knowledgebank to equip rag agent with a (set of) knowledge
    # corresponding to its knowledge_id_list
    for agent in scientists:
        knowledge_bank.equip(agent, agent.knowledge_id_list)

    team_list = []
    for agent in survivors:
        team_agent = []
        team_index = []
        team_index.append(agent.name)
        team_agent.append(team_index)
        team_list.append(team_agent)

    # start the game
    for _ in range(1, MAX_GAME_ROUND + 1):
        # night phase, werewolves discuss
        for agent_index in range(len(scientists)):
            hint = HostMsg(content=Prompts.ask_choice.format_map(
                {
                    "Scientist_name": scientists[agent_index].name,
                    "All_team": team_description(team_list[agent_index])
                },
            ),
            )
            set_parsers(scientists[agent_index], Prompts.scientist_self_discuss_parser)
            x = scientists[agent_index](hint)
            if x.metadata.get("finish_selection", False):
                break

            # werewolves vote
            set_parsers(scientists[agent_index], Prompts.scientist_select_parser)
            hint = HostMsg(content=Prompts.to_scientist_select)
            team_candidate = extract_scientist_names(scientists[agent_index](hint).content)[0]
            # broadcast the result to werewolves
            agent_candidate = []
            for agent_num in scientists:
                if agent_num.name in team_candidate:
                    agent_candidate.append(agent_num)
            team_index = []
            for agent in agent_candidate:
                hint = HostMsg(content=Prompts.to_scientist_choice.format_map({
                    "scientist_name": agent.name,
                    "inviter_name": scientists[agent_index].name,
                    "personal information" : agent.sys_prompt
                }))
                set_parsers(agent, Prompts.scientist_invite_parser)
                if agent(hint).metadata.get("accept", False):
                    team_index.append(agent.name)
            is_contained == False
            for agent_list in team_list:
                is_contained = any(sublist == team_index for sublist in agent_list)
                if is_contained == True:
                    break
            if is_contained == False:
                team_list[agent_index].append(team_index)

            scientists[agent_index](HostMsg(content=team_description(team_list[agent_index])))





        # # witch
        # healing_used_tonight = False
        # if witch in survivors:
        #     if healing:
        #         hint = HostMsg(
        #             content=Prompts.to_witch_resurrect.format_map(
        #                 {
        #                     "witch_name": witch.name,
        #                     "dead_name": dead_player[0],
        #                 },
        #             ),
        #         )
        #         set_parsers(witch, Prompts.witch_resurrect_parser)
        #         if witch(hint).metadata.get("resurrect", False):
        #             healing_used_tonight = True
        #             dead_player.pop()
        #             healing = False
        #             HostMsg(content=Prompts.to_witch_resurrect_yes)
        #         else:
        #             HostMsg(content=Prompts.to_witch_resurrect_no)

        #     if poison and not healing_used_tonight:
        #         set_parsers(witch, Prompts.witch_poison_parser)
        #         x = witch(HostMsg(content=Prompts.to_witch_poison))
        #         if x.metadata.get("eliminate", False):
        #             dead_player.append(extract_name_and_id(x.content)[0])
        #             poison = False

        # # seer
        # if seer in survivors:
        #     hint = HostMsg(
        #         content=Prompts.to_seer.format(seer.name, n2s(survivors)),
        #     )
        #     set_parsers(seer, Prompts.seer_parser)
        #     x = seer(hint)

        #     player, idx = extract_name_and_id(x.content)
        #     role = "werewolf" if roles[idx] == "werewolf" else "villager"
        #     hint = HostMsg(content=Prompts.to_seer_result.format(player, role))
        #     seer.observe(hint)

        # survivors, wolves = update_alive_players(
        #     survivors,
        #     wolves,
        #     dead_player,
        # )
        # if check_winning(survivors, wolves, "Moderator"):
        #     break

        # # daytime discussion
        # content = (
        #     Prompts.to_all_danger.format(n2s(dead_player))
        #     if dead_player
        #     else Prompts.to_all_peace
        # )
        # hints = [
        #     HostMsg(content=content),
        #     HostMsg(content=Prompts.to_all_discuss.format(n2s(survivors))),
        # ]
        # with msghub(survivors, announcement=hints) as hub:
        #     # discuss
        #     set_parsers(survivors, Prompts.survivors_discuss_parser)
        #     x = sequentialpipeline(survivors)

        #     # vote
        #     set_parsers(survivors, Prompts.survivors_vote_parser)
        #     hint = HostMsg(content=Prompts.to_all_vote.format(n2s(survivors)))
        #     votes = [
        #         extract_name_and_id(_(hint).content)[0] for _ in survivors
        #     ]
        #     vote_res = majority_vote(votes)
        #     # broadcast the result to all players
        #     result = HostMsg(content=Prompts.to_all_res.format(vote_res))
        #     hub.broadcast(result)

        #     survivors, wolves = update_alive_players(
        #         survivors,
        #         wolves,
        #         vote_res,
        #     )

        #     if check_winning(survivors, wolves, "Moderator"):
        #         break

        #     hub.broadcast(HostMsg(content=Prompts.to_all_continue))


if __name__ == "__main__":
    main()
