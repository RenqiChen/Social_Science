# -*- coding: utf-8 -*-
"""Used to record prompts, will be replaced by configuration"""
from agentscope.parsers.json_object_parser import MarkdownJsonDictParser


class Prompts:
    """Prompts for werewolf game"""

    ask_choice = (
        "{Scientist_name}, now you are at the team: {All_team}. You can find new scientists to organize a team or do nothing."
    )

    to_wolves = (
        "{}, if you are the only werewolf, eliminate a player. Otherwise, "
        "discuss with your teammates and reach an agreement."
    )

    wolves_discuss_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "what you speak",
            "finish_discussion": "whether the discussion reached an "
            "agreement or not (true/false)",
        },
        required_keys=["thought", "speak", "finish_discussion"],
        keys_to_memory="speak",
        keys_to_content="speak",
        keys_to_metadata=["finish_discussion"],
    )

    scientist_self_discuss_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "what you speak",
            "finish_select": "whether you want to find partners or not (true/false)",
        },
        required_keys=["thought", "speak", "finish_select"],
        keys_to_memory="speak",
        keys_to_content="speak",
        keys_to_metadata=["finish_select"],
    )

    to_scientist_select = "Who will you want to select as your partners?"
    "Please provide their names in the following format: <select> Name1, Name2, Name3 </select>"


    wolves_vote_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "vote": "player_name",
        },
        required_keys=["thought", "vote"],
        keys_to_memory="vote",
        keys_to_content="vote",
    )

    scientist_select_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "select": "scientist_names",
        },
        required_keys=["thought", "select"],
        keys_to_memory="select",
        keys_to_content="select",
    )

    to_wolves_res = "The player with the most votes is {}."

    to_witch_resurrect = (
        "{witch_name}, you're the witch. Tonight {dead_name} is eliminated. "
        "Would you like to resurrect {dead_name}?"
    )
    to_scientist_choice = (
        "{scientist_name}, {inviter_name} invites you to join his team. His personal information is {personal information}"
        "Would you like to join him?"
    )

    to_witch_resurrect_no = "The witch has chosen not to resurrect the player."
    to_witch_resurrect_yes = "The witch has chosen to resurrect the player."

    witch_resurrect_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "whether to resurrect the player and the reason",
            "resurrect": "whether to resurrect the player or not (true/false)",
        },
        required_keys=["thought", "speak", "resurrect"],
        keys_to_memory="speak",
        keys_to_content="speak",
        keys_to_metadata=["resurrect"],
    )

    scientist_invite_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "whether to accept the invitation from the scientist and the reason",
            "accept": "whether to accept the invitation from the scientist or not (true/false)",
        },
        required_keys=["thought", "speak", "accept"],
        keys_to_memory="speak",
        keys_to_content="speak",
        keys_to_metadata=["accept"],
    )


    to_witch_poison = (
        "Would you like to eliminate one player? If yes, "
        "specify the player_name."
    )

    witch_poison_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "what you speak",
            "eliminate": "whether to eliminate a player or not (true/false)",
        },
        required_keys=["thought", "speak", "eliminate"],
        keys_to_memory="speak",
        keys_to_content="speak",
        keys_to_metadata=["eliminate"],
    )

    to_seer = (
        "{}, you're the seer. Which player in {} would you like to check "
        "tonight?"
    )

    seer_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "player_name",
        },
        required_keys=["thought", "speak"],
        keys_to_memory="speak",
        keys_to_content="speak",
    )

    to_seer_result = "Okay, the role of {} is a {}."

    to_all_danger = (
        "The day is coming, all the players open your eyes. Last night, "
        "the following player(s) has been eliminated: {}."
    )

    to_all_peace = (
        "The day is coming, all the players open your eyes. Last night is "
        "peaceful, no player is eliminated."
    )

    to_all_discuss = (
        "Now the alive players are {}. Given the game rules and your role, "
        "based on the situation and the information you gain, to vote a "
        "player eliminated among alive players and to win the game, what do "
        "you want to say to others? You can decide whether to reveal your "
        "role."
    )

    survivors_discuss_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "speak": "what you speak",
        },
        required_keys=["thought", "speak"],
        keys_to_memory="speak",
        keys_to_content="speak",
    )

    survivors_vote_parser = MarkdownJsonDictParser(
        content_hint={
            "thought": "what you thought",
            "vote": "player_name",
        },
        required_keys=["thought", "vote"],
        keys_to_memory="vote",
        keys_to_content="vote",
    )

    to_all_vote = (
        "Given the game rules and your role, based on the situation and the"
        " information you gain, to win the game, it's time to vote one player"
        " eliminated among the alive players. Which player do you vote to "
        "kill?"
    )

    to_all_res = "{} has been voted out."

    to_all_wolf_win = (
        "The werewolves have prevailed and taken over the village. Better "
        "luck next time!"
    )

    to_all_village_win = (
        "The game is over. The werewolves have been defeated, and the village "
        "is safe once again!"
    )

    to_all_continue = "The game goes on."
