import sys
import torch.nn.functional
import os
import numpy as np
import json
import re
import random
import ollama
from functools import partial
import faiss

sys.path.append('../agentscope-main/src')
import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.agents import SciAgent
from agentscope.memory import TemporaryMemory
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline

from sci_team.SciTeam import Team
from utils.prompt import Prompts
from utils.scientist_utils import (
    extract_scientist_names,
    team_description,
    n2s,
    convert_you_to_other,
    team_description_detail,
    format_msg,
    formated_msg2str,
    read_txt_files_as_dict,
    extract_between_json_tags,
    extract_metrics,
    paper_search,
    strip_non_letters,
    save2database,
    count_team,
    top_three_indices,
    extract_first_number,
    most_frequent_element
)

class Platform:
    r"""Platform."""

    def __init__(self,
                 model_configuration: str = './configs/model_configs.json',
                 agent_num: int = 1,
                 root_dir: str = '/home/bingxing2/ailab/group/ai4agr/shy/s4s',
                 paper_folder_path: str = "/home/bingxing2/ailab/group/ai4agr/crq/SciSci/papers",
                 future_paper_folder_path: str = "/home/bingxing2/ailab/group/ai4agr/crq/SciSci/papers_future",
                 author_info_dir: str = 'authors',
                 adjacency_matrix_dir: str = 'authors_degree_ge50_from_year2000to2010',
                 agent_model_config_name: str = 'ollama_llama3.1_8b',
                 review_model_config_name: str = 'ollama_llama3.1_70b',
                 knowledgeBank_config_dir: str = "./configs/knowledge_config.json",
                 log_dir: str = 'logs',
                 info_dir: str = "team_info",
                 hop_num: int = 2,
                 group_max_discuss_iteration: int = 7, # 6， 7
                 recent_n_team_mem_for_retrieve: int = 1,
                 team_limit: int = 2,
                 check_iter: int = 5,
                 review_num: int = 2,
                 max_teammember: int = 3, # 3， 7， 9
                 cite_number: int = 8,
                 default_mark: int = 4,
                 skip_check: bool = False,
                 over_state: int = 8,
                 begin_state: int = 1
                 ):
        self.agent_num = agent_num
        self.paper_folder_path = paper_folder_path
        self.paper_future_folder_path = future_paper_folder_path
        self.author_info_dir = os.path.join(root_dir, author_info_dir)
        self.adjacency_matrix_dir = os.path.join(root_dir, adjacency_matrix_dir)
        self.group_max_discuss_iteration = group_max_discuss_iteration
        self.recent_n_team_mem_for_retrieve = recent_n_team_mem_for_retrieve
        # how many teams for one agent is allowed
        self.team_limit = team_limit
        # how many times to try paper search
        self.check_iter = check_iter
        # the number of reviewer
        self.reviewer_num = review_num
        # the max team member in a team
        self.max_teammember = max_teammember
        # cite how many paper when generating the idea
        self.cite_number = cite_number
        # default review mark
        self.default_mark = default_mark
        # check novelty
        self.skip_check = skip_check
        # current state for the over of team activity
        self.over_state = over_state
        # current state for the begin of team activity
        self.begin_state = begin_state
        # output dir
        self.log_dir = log_dir
        self.info_dir = info_dir

        # for quality, the team of one member will think more times
        self.think_times = max_teammember+1

        # author2paper file: dict{'authorID':[paperID1, paperID2, ...]}
        with open('{}/author2paper.json'.format(root_dir), 'r') as file:
            self.author2paper = json.load(file)

        # load k-hop adjacency matrix
        self.degree_int2word = ['one', 'two', 'three', 'four', 'five']
        # self.adjacency_matrix = np.loadtxt(
        #     '{}/{}-hop_adj_matrix.txt'.format(self.adjacency_matrix_dir, self.degree_int2word[hop_num-1]), dtype=int)
        self.adjacency_matrix = np.loadtxt(
            '{}/adjacency.txt'.format(self.adjacency_matrix_dir), dtype=int)

        # check if agent_num is valid
        if self.agent_num is None:
            self.agent_num = len(self.adjacency_matrix)
        else:
            assert self.agent_num <= len(self.adjacency_matrix)

        # load agentID2authorID file: dict{'agentID': 'authorID'}
        with open('{}/agentID2authorID.json'.format(self.adjacency_matrix_dir), 'r') as file:
            self.agentID2authorID = json.load(file)

        # init agentscope
        agentscope.init(model_configs=model_configuration)

        # init knowledge bank
        if knowledgeBank_config_dir is not None:
            self.knowledge_bank = self.init_knowledgeBank(knowledgeBank_config_dir)

        # init agent pool
        self.agent_pool = [self.init_agent(str(agent_id), agent_model_config_name, '/home/bingxing2/ailab/group/ai4agr/crq/SciSci/books/author_{}.txt'.format(agent_id)) for agent_id in range(len(self.adjacency_matrix))]
        self.reviewer_pool = [self.init_reviewer(str(agent_id), review_model_config_name) for agent_id in range(self.reviewer_num)]
        self.id2agent = {}
        for agent in self.agent_pool:
            self.knowledge_bank.equip(agent, agent.knowledge_id_list)
            self.id2agent[agent.name] = agent
        # team pool
        self.team_pool = []
        agent_id = 1
        for agent in self.agent_pool[:self.agent_num]:
            team_agent = []
            team_index = []
            team_index.append(agent.name)
            team_dic = Team(team_name = str(agent_id)+','+str(1),
                            log_dir = self.log_dir,
                            info_dir = self.info_dir)
            team_dic.teammate = team_index
            team_agent.append(team_dic)
            self.team_pool.append(team_agent)
            agent_id = agent_id + 1


        # init hint
        self.HostMsg = partial(Msg, name="user", role="user", echo=True)

        # paper embedding list
        cpu_index = faiss.read_index("/home/bingxing2/ailab/group/ai4agr/crq/SciSci/faiss_index.index")  # 加载索引
        res = faiss.StandardGpuResources()  # 为 GPU 资源分配
        self.gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)  # 将索引移到 GPU

        cpu_future_index = faiss.read_index("/home/bingxing2/ailab/group/ai4agr/crq/SciSci/faiss_index_future.index")  # 加载索引
        future_res = faiss.StandardGpuResources()  # 为 GPU 资源分配
        self.gpu_future_index = faiss.index_cpu_to_gpu(future_res, 0, cpu_future_index)  # 将索引移到 GPU

        self.paper_dicts = read_txt_files_as_dict(self.paper_folder_path)
        self.paper_future_dicts = read_txt_files_as_dict(self.paper_future_folder_path)

    def init_reviewer(self, agent_id, agent_model_config_name):
        agent = SciAgent(
            name='Paper Reviewer{}'.format(agent_id),
            model_config_name=agent_model_config_name,
            sys_prompt=Prompts.prompt_review_system,
        )
        return agent

    def init_agent(self, agent_id, agent_model_config_name, information_path):
        # load author info
        with open(information_path, 'r') as file:
            prompt = file.read()

        agent = SciAgent(
            name='Scientist{}'.format(agent_id),
            model_config_name=agent_model_config_name,
            sys_prompt=prompt,
            knowledge_id_list = ["author_information"],
            similarity_top_k=2,
            log_retrieval=False,
            recent_n_mem_for_retrieve=2,
        )

        return agent

    def init_knowledgeBank(self, knowledgeBank_config_dir):
        knowledge_bank = KnowledgeBank(configs="configs/knowledge_config.json")

        # alternatively, we can easily input the configs to add data to RAG
        knowledge_bank.add_data_as_knowledge(
            knowledge_id="author_information",
            emb_model_name="ollama_embedding-mxbai-embed-large",
            data_dirs_and_types={
                "/home/bingxing2/ailab/group/ai4agr/crq/SciSci/books": [".txt"],
            },
        )
        return knowledge_bank

    def select_coauthors(self,):
        team_list = self.team_pool
        scientists = self.agent_pool[:self.agent_num]
        # decide whether the scientist wants to find partners
        for agent_index in range(len(scientists)):
            # avoid too many teams
            if count_team(team_list[agent_index], self.over_state)>=self.team_limit:
                # choose to enforcely add the owner as a team
                if team_list[agent_index][0].state==1:
                    team_list[agent_index][0].state=2
                continue
            scientists[agent_index].sys_prompt = scientists[agent_index].sys_prompt + Prompts.role
            hint = self.HostMsg(content=Prompts.ask_choice.format_map(
                {
                    "Scientist_name": scientists[agent_index].name,
                    "All_team": team_description(team_list[agent_index], self.over_state)
                },
            ),
            )
            x = scientists[agent_index].reply(hint)
            team_list[agent_index][0].log_dialogue('user',hint.content)
            team_list[agent_index][0].log_dialogue(scientists[agent_index].name,x.content)
            match = re.search(r'action\s*(\d+)', x.content, re.IGNORECASE)

            # when action2, the agent choose to act independently
            if int(match.group(1))==2:
                print("Single Agent Independently!")
                team_list[agent_index][0].state=2
                continue

            # use prompts to select scientists
            scientist = scientists[agent_index].name
            name = int(scientist[9:])

            arr = self.adjacency_matrix[name,:]
            arr[agent_index] = 0
            probabilities = arr / np.sum(arr)

            selected_indices = np.random.choice(len(arr), size=self.max_teammember, p=probabilities, replace=False)

            team_candidate = []
            for i in range(len(selected_indices)):
                team_candidate.append(f"Scientist{selected_indices[i]}")

            print(team_candidate)
            team_list[agent_index][0].log_dialogue(scientists[agent_index].name,','.join(team_candidate))
            is_contained = False
            for agent_list in team_list:
                for sublist in agent_list:
                    if set(sublist.teammate) == set(team_candidate) and sublist.state != self.over_state:
                        is_contained = True
                        break
                if is_contained == True:
                    break
            if is_contained == True:
                continue
            # ask each scientist to decide whether to join
            agent_candidate = self.id_to_agent(team_candidate)
            # create new team
            team_index = []
            team_index.append(scientists[agent_index].name)
            for agent in agent_candidate:
                if agent.name == scientists[agent_index].name:
                    continue
                hint = self.HostMsg(content=Prompts.to_scientist_choice.format_map({
                    "inviter_name": scientists[agent_index].name,
                    "team_member": str(team_index),
                    "personal information" : convert_you_to_other(scientists[agent_index].sys_prompt)
                }))
                # set_parsers(agent, Prompts.scientist_invite_parser)
                pattern = re.compile(r'action\s*1', re.IGNORECASE)
                # action1 means a scientist accepts the invitance
                x = agent.reply(hint, use_memory=False, use_RAG=False)
                if pattern.search(extract_between_json_tags(x.content,num=1)):
                    team_index.append(agent.name)
                team_list[agent_index][0].log_dialogue('user',hint.content)
                team_list[agent_index][0].log_dialogue(agent.name,x.content)
            # delete repeated teams
            is_contained = False
            for agent_list in team_list:
                for sublist in agent_list:
                    if set(sublist.teammate) == set(team_index) and sublist.state != self.over_state:
                        is_contained = True
                        break
                if is_contained == True:
                    break
            if is_contained == False:
                team_dic = Team(team_name = str(agent_index+1)+','+str(len(self.team_pool[agent_index])+1),
                                log_dir = self.log_dir,
                                info_dir = self.info_dir)
                team_dic.state=2
                team_dic.teammate = team_index
                team_list[agent_index].append(team_dic)

                # connetion between collaborators will be closer
                for member in team_dic.teammate:
                    if int(member[9:])!=agent_index:
                        self.adjacency_matrix[agent_index,int(member[9:])]=self.adjacency_matrix[agent_index,int(member[9:])]+0.2
                        self.adjacency_matrix[int(member[9:]),agent_index]=self.adjacency_matrix[int(member[9:]),agent_index]+0.2
                # summary current teams in memory
                scientists[agent_index].prompt_reply(self.HostMsg(content=team_description_detail(team_list[agent_index], self.agent_pool, self.over_state)))
            else:
                continue
        return team_list

    def group_discuss(self, team_temp, prompt :str = None):
        # prompt is used to start and guide the discussion
        # for each turn, in group_discuss, all dialogue history is stored in dialogue_history but not in agent memory
        # after finishing each discussion turn, agent1 will summarize dialogue_history and add a summarization into team_history
        team = team_temp
        # get team_history
        team_history = team.memory
        # get teammate
        teammate = self.id_to_agent(team.teammate)
        # init dialogue_history
        dialogue_history = TemporaryMemory(None)
        # init exit state
        exit = False
        # output return dialogue history, summarization of the last turn, and memory of the last turn
        output = {}
        # start discussing
        if len(teammate)==1:
            group_max_discuss_iteration = self.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = self.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            said = []
            # init turn_memory for each turn
            turn_history = TemporaryMemory(None)
            agent_num = 0
            for agent in teammate:
                if agent.name in said:
                    continue
                else:
                    said.append(agent.name)
                agent_prompt = format_msg(
                    # current team
                    Msg(name="current team members", role="user", content=','.join(team.teammate)),
                    # team history
                    Msg(name="Summarizations of previous team discussions", role="user", content='')
                    if team_history.size()>0 else None,
                    team_history.get_memory(recent_n=self.recent_n_team_mem_for_retrieve),
                    # prompt
                    Msg(name="user", role="user", content=prompt),
                    # dialogue history
                    Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                    if dialogue_history.size()>0 else None,
                    dialogue_history.get_memory(recent_n=turn),
                    # turn history
                    Msg(name="Discussions in this turn", role="user", content='')
                    if turn_history.size()>0 else None,
                    turn_history.get_memory(recent_n=agent_num)
                )
                # add reply to turn_history
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False)
                if reply.content!=None and len(reply.content)>0:
                    team.log_dialogue(agent.name,reply.content)
                involved_scientist = extract_scientist_names(reply.content)
                print(involved_scientist)
                # judge whether someone is called to join the team
                for scientist_index in involved_scientist:
                    if scientist_index not in team.teammate:
                        if "by the way" in reply.content or "By the way" in reply.content:
                            hint = Msg(name=team.teammate[0],role="user",content=reply.content)
                            # invite new team member to comment
                            x = self.id2agent[scientist_index].reply(hint, use_memory=False, use_RAG=False)
                            if x.content is not None:
                                said.append(scientist_index)
                                team.teammate.append(scientist_index)
                                team.log_dialogue(self.id2agent[scientist_index].name, x.content)
                                teammate.append(self.id2agent[scientist_index])

                turn_history.add(reply)
                agent_num = agent_num + 1
                # discussion is finished
                if 'exit' in reply:
                    exit = True
                    break

            # summarize this turn's discussion
            history = format_msg(
                # team history
                Msg(name="Summarizations of previous team discussions", role="user", content='')
                if team_history.size()>0 else None,
                team_history.get_memory(recent_n=self.recent_n_team_mem_for_retrieve),
                # dialogue history
                Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                if dialogue_history.size()>0 else None,
                dialogue_history.get_memory(recent_n=turn),
            )
            x = teammate[0].summarize(history = history, content = turn_history.get_memory(recent_n=agent_num))
            team.log_dialogue(teammate[0].name, x.content)
            turn_summarization = Msg(name="summarizations of turn{}".format(turn+1), role="user",
                                     content=x.content)

            if exit or turn==group_max_discuss_iteration-1:
                output['last_turn_summarization'] = turn_summarization
                output['last_turn_history'] = turn_history
                break
            else:
                dialogue_history.add(turn_summarization)

        output['dialogue_history'] = dialogue_history
        team.teammate = self.agent_to_id(teammate)
        return team, output

    def select_topic(self, team):
        # prompt to start discussing select_topic
        team, discuss_result = self.group_discuss(team, Prompts.to_start_topic_discussion)
        print('finish group discuss')
        team_history = team.memory
        dialogue_history = discuss_result['dialogue_history']
        last_turn_history = discuss_result['last_turn_history']
        last_turn_summarization = discuss_result['last_turn_summarization']

        answer_prompt = format_msg(
            # team history
            Msg(name="Summarizations of previous team discussions", role="user", content='')
            if team_history.size()>0 else None,
            team_history.get_memory(recent_n=self.recent_n_team_mem_for_retrieve),
            # dialogue history
            Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
            if dialogue_history.size()>0 else None,
            dialogue_history.get_memory(recent_n=self.group_max_discuss_iteration),
            # turn history
            Msg(name="Discussions in this turn", role="user", content='')
            if last_turn_history.size()>0 else None,
            last_turn_history.get_memory(recent_n=last_turn_history.size()),
            # answer_prompt
            Msg(name="user", role="user", content=Prompts.to_ask_if_ready_give_topic)
        )
        answer = self.id2agent[team.teammate[0]].prompt_reply(answer_prompt, add_memory = False, use_memory=False)
        team.log_dialogue('user',self.id2agent[team.teammate[0]].model.format(answer_prompt))
        team.log_dialogue(self.id2agent[team.teammate[0]].name, answer.content)
        answer_pattern = re.compile(r'action\s*1', re.IGNORECASE)

        # update dialogue history
        dialogue_history.add(last_turn_summarization)
        dialogue_history.add(answer)

        # check whether agent is ready to answer
        if answer_pattern.search(answer.content) or team_history.size()>=1:
            team.state = 3
            history_prompt = format_msg(
                # team history
                Msg(name="Summarizations of previous team discussions", role="user", content='')
                if team_history.size()>0 else None,
                team_history.get_memory(recent_n=self.recent_n_team_mem_for_retrieve),
                # dialogue history
                Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                if dialogue_history.size()>0 else None,
                dialogue_history.get_memory(recent_n=self.group_max_discuss_iteration),
                # turn history
                Msg(name="Discussions in this turn", role="user", content='')
                if last_turn_history.size()>0 else None,
                last_turn_history.get_memory(recent_n=last_turn_history.size()),
            )
            topic_prompt = format_msg(
                # answer,
                # topic_prompt
                Msg(name="user", role="user", content=Prompts.to_ask_topic.replace("[history_prompt]", formated_msg2str(history_prompt)))
            )
            topic = self.id2agent[team.teammate[0]].prompt_reply(topic_prompt, add_memory = False)
            team.log_dialogue(team.teammate[0],topic.content)
            team.topic = extract_between_json_tags(topic.content,num=1)
            team.topic = strip_non_letters(team.topic.split("Topic")[1])

            # update dialogue history
            dialogue_history.add(topic)

        # update team_history
        history = format_msg(
            # team history
            Msg(name="Summarizations of previous team discussions", role="user", content='')
            if team_history.size()>0 else None,
            team_history.get_memory(recent_n=self.recent_n_team_mem_for_retrieve)
        )
        team_history.add(Msg(name="summarizations of one topic discussion", role="user",
                             content=self.id2agent[team.teammate[0]].summarize(history = history, content = dialogue_history.get_memory(recent_n=self.group_max_discuss_iteration))))
        team.memory = team_history
        return team

    def generate_idea(self, team):
        topic = team.topic
        old_idea = None
        best_idea = None
        idea_list = []
        mark_list = []
        # search related paper about the topic
        selected_topics = strip_non_letters(topic.split("Selected Topics:")[-1])
        paper_reference, cite_paper = self.reference_paper(selected_topics, self.cite_number)

        teammate = self.id_to_agent(team.teammate)
        idea_judge = True

        if len(teammate)==1:
            group_max_discuss_iteration = self.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = self.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            # discuss the idea
            for agent in teammate:
                idea_prompt = Prompts.prompt_task+Prompts.prompt_existing_idea.format(old_idea)+ \
                              Prompts.prompt_topic.format(selected_topics)+Prompts.prompt_reference.format(paper_reference)+ \
                              Prompts.prompt_response
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=idea_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                team.log_dialogue('user',idea_prompt)
                team.log_dialogue(agent.name,reply.content)
                old_idea = extract_between_json_tags(reply.content, num=1)
                if "Title" in old_idea:
                    idea_key = old_idea.split("Title")[1]
                    idea_key = strip_non_letters(idea_key.split("Experiment")[0])
                else:
                    idea_key = old_idea.split("Idea")[1]
                    idea_key = strip_non_letters(idea_key.split("Experiment")[0])
                paper_reference, cite_paper_new = self.reference_paper(idea_key, self.cite_number)
                cite_paper = list(set(cite_paper).union(cite_paper_new))

                # find the metric
                split_keywords = ['Interestingness', 'Feasibility', 'Novelty']
                metrics = extract_metrics(old_idea, split_keywords)
                if best_idea != None:
                    if old_idea == best_idea:
                        idea_judge=True
                        print("exit early!!!!!!")
                        break
                    best_metrics = extract_metrics(best_idea, split_keywords)
                    old_count = 0
                    best_count = 0
                    for split_keywork in split_keywords:
                        if metrics[split_keyword]==None:
                            break
                        if split_keyword=='Novelty':
                            old_count = old_count + 2*metrics[split_keyword]
                        else:
                            old_count = old_count + metrics[split_keyword]
                        if best_metrics[split_keyword]==None:
                            break
                        best_count = best_count + best_metrics[split_keyword]
                    if old_count>=best_count:
                        best_idea = old_idea
                        idea_list.append(old_idea)
                        mark_list.append(old_count)
                else:
                    idea_list.append(old_idea)
                    best_idea = old_idea
                # if all metrics are larger than 8, then over
                for split_keyword in split_keywords:
                    if metrics[split_keyword]==None:
                        break
                    if metrics[split_keyword]<11:
                        idea_judge=False
                        break
                if idea_judge:
                    best_idea=old_idea
                    break
            if idea_judge:
                break
        if team.idea == None:
            if len(idea_list)>3:
                indices = top_three_indices(mark_list)
                idea_list = [idea_list[i] for i in indices]
                team.idea = idea_list
            else:
                team.idea = idea_list
        print("Candidate Idea:")
        print(team.idea)
        if self.skip_check:
            team.state=5
        else:
            team.state=4
        team.citation_id = cite_paper
        print(len(team.citation_id))
        return team

    def check_novelty(self, team):
        existing_idea = team.idea
        idea_choices = ""
        for idea_index in range(len(existing_idea)):
            idea = existing_idea[idea_index]
            idea_choices = idea_choices+"Idea "+str(idea_index)+":\n"+idea+"\n"
        related_papers = []
        for idea_index in existing_idea:
            title = idea_index.split("Title")[1]
            title = strip_non_letters(title.split("Experiment")[0])
            if len(existing_idea)==3:
                cite_number = 3
            else:
                cite_number = 5
            _, related_paper = self.reference_paper(title, cite_number)

            related_papers = list(set(related_papers).union(related_paper))

        paper_reference = ""
        for id in range(len(related_papers)):
            paper_index = related_papers[id]
            paper_reference = paper_reference+"Paper {}:".format(id+1)+"\n"
            paper_reference = paper_reference+"Title: "+self.paper_dicts[paper_index]['title']+"\n"
            paper_reference = paper_reference+"Abstract: "+self.paper_dicts[paper_index]['abstract']+"}"+"\n"

        teammate = self.id_to_agent(team.teammate)
        choice_list = []
        if len(teammate)==1:
            group_max_discuss_iteration = self.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = self.group_max_discuss_iteration
        for turn in range(group_max_discuss_iteration):
            # discuss the idea
            for agent in teammate:
                idea_novelty_prompt = Prompts.prompt_idea_check+Prompts.prompt_idea_check_response.replace("{existing_idea}", idea_choices).replace("{last_query_results}",paper_reference)
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=idea_novelty_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                team.log_dialogue('user',idea_novelty_prompt)
                team.log_dialogue(agent.name,reply.content)
                old_idea = extract_between_json_tags(reply.content, num=1)
                idea_choice = extract_first_number(old_idea)
                if idea_choice == None:
                    idea_choice = 0
                choice_list.append(int(idea_choice))

        final_choice = most_frequent_element(choice_list)
        if final_choice<0 or final_choice>=len(existing_idea):
            final_choice = len(existing_idea)-1
        try:
            team.idea = existing_idea[final_choice]
        except:
            team.idea = existing_idea[0]
        print("Final Idea:")
        print(team.idea)
        team.state=5
        return team

    def generate_abstract(self, team):
        idea = team.idea
        old_abstract = team.abstract
        teammate = self.id_to_agent(team.teammate)

        if len(teammate)==1:
            group_max_discuss_iteration = self.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = self.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            # discuss the abstract
            for agent in teammate:
                if old_abstract == None:
                    abstract_prompt = Prompts.prompt_abstract+"\n"+idea+ \
                                      "\n"+Prompts.prompt_abstract_requirement+"\n"+Prompts.prompt_abstract_response
                else:
                    # the paper is not reviewed by reviewer
                    if team.paper_review == None:
                        # the paper is not reviewer by the team member
                        if team.self_review == None:
                            prompt_abstract_judgement = Prompts.prompt_abstract_judgement.replace("[Insert abstract here]",old_abstract)
                            abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                        else:
                            prompt_abstract_judgement = Prompts.prompt_abstract_judgement_self.replace("[Insert abstract here]",old_abstract)
                            prompt_abstract_judgement = prompt_abstract_judgement.replace("[Insert self_review comments]", team.self_review)
                            abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                    else:
                        prompt_abstract_judgement = Prompts.prompt_abstract_judgement_after_review.replace("[Insert Reviewer comments]",team.paper_review)
                        prompt_abstract_judgement = prompt_abstract_judgement.replace("[Insert abstract here]",old_abstract)
                        abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=abstract_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                team.log_dialogue(agent.name, reply.content)
                old_abstract = extract_between_json_tags(reply.content, num=1)
                if old_abstract == None:
                    old_abstract = reply.content

        related_papers = []

        Abstract = strip_non_letters(old_abstract.split("Abstract")[1])
        query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=Abstract)
        query_vector = np.array([query_vector['embedding']])

        D_future, I_future = self.gpu_future_index.search(query_vector, int(self.cite_number/2))
        D, I = self.gpu_index.search(query_vector, int(self.cite_number/2))

        for id in range(len(I_future[0])):
            paper_title = self.paper_future_dicts[I_future[0][id]]['title']
            paper_abstract = self.paper_future_dicts[I_future[0][id]]['abstract']
            paper_year = self.paper_future_dicts[I_future[0][id]]['year']
            paper_citation = self.paper_future_dicts[I_future[0][id]]['citation']
            paper_index = {}
            paper_index['title'] = paper_title
            paper_index['abstract'] = paper_abstract
            paper_index['year'] = paper_year
            paper_index['citation'] = paper_citation
            related_papers.append(paper_index)

        for id in range(len(I[0])):
            paper_title = self.paper_dicts[I[0][id]]['title']
            paper_abstract = self.paper_dicts[I[0][id]]['abstract']
            paper_year = self.paper_dicts[I[0][id]]['year']
            paper_citation = self.paper_dicts[I[0][id]]['citation']
            paper_index = {}
            paper_index['title'] = paper_title
            paper_index['abstract'] = paper_abstract
            paper_index['year'] = paper_year
            paper_index['citation'] = paper_citation
            related_papers.append(paper_index)

        # eval with embedding similarity
        abs = []
        our_abs = strip_non_letters(old_abstract.split('Abstract')[1])
        abs.append(ollama.embeddings(model="mxbai-embed-large", prompt=our_abs)['embedding'])
        for paper_id in range(len(related_papers)):
            related_astract = related_papers[paper_id]['abstract']
            abs.append(ollama.embeddings(model="mxbai-embed-large", prompt=related_astract)['embedding'])

        sim = []
        for emb_id in range(1, len(abs)):
            sim.append(torch.nn.functional.cosine_similarity(torch.tensor(abs[0]).unsqueeze(0),
                                                             torch.tensor(abs[emb_id]).unsqueeze(0), dim=-1)[0].item())
        team.log_dialogue('embedding similarity', str(sim))

        team.log_dialogue('faiss_distance', str(D))
        team.log_dialogue('faiss_distance_future', str(D_future))

        # eval with LLM
        print('related papers:')
        print(len(related_papers))
        if len(related_papers)>0:
            team.log_dialogue('arxiv',related_papers)
        # find paper successfully
        if len(related_papers)>0:
            abstract_check_prompt = Prompts.prompt_abstract_check.replace("[Insert your abstract here]", old_abstract)
            cite_abstract = ""
            word = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T']
            split_keywords = []
            for paper_id in range(len(related_papers)):
                cite_abstract = cite_abstract+str(paper_id+1)+". Abstract {}: ".format(word[paper_id])+"Title: "+related_papers[paper_id]['title']+"\n"+"Abstract: "+related_papers[paper_id]['abstract']+"\n"
                split_keywords.append('Written Abstract vs {}'.format(word[paper_id]))
            abstract_check_prompt = abstract_check_prompt.replace("[Insert ref abstract here]", cite_abstract)
            abstract_check_prompt = abstract_check_prompt+"\n"+Prompts.prompt_response_check
            agent_prompt = format_msg(
                # prompt
                Msg(name="user", role="user", content=abstract_check_prompt),
            )
            reply = teammate[0].prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
            team.log_dialogue(teammate[0].name, reply.content)
            print("abstract_check:")
            print(split_keywords)
            comparison = extract_between_json_tags(reply.content)
            metric = extract_metrics(comparison, split_keywords=split_keywords)
            abstract_use = True
            for split_keyword in split_keywords:
                if metric[split_keyword]>=70:
                    abstract_use = False
                    team.abstract = old_abstract
                    break
            team.abstract = old_abstract
            print('Final Abstract:')
            print(team.abstract)
            # stop early
            team.state=7

            # do not stop early

            # if abstract_use:
            #     team.state=6
            #     team.self_review=None
            # # if the abstract is too similar one time, go to revise, otherwise back to generate idea
            # else:
            #     if team.self_review!=None:
            #         team.state=3
            #         team.idea = None
            #         team.abstract = None
            #         team.citation_id = None
            #         team.self_review = None
            #         team.paper_review = None
            #     else:
            #         team.self_review = reply.content

        else:
            print('Check Fail!!!!!!')
            if team.abstract == None:
                team.abstract = old_abstract
                print('Final Abstract:')
                print(team.abstract)
                team.state=6
        return team

    def generate_review(self, team):
        # paper reviewer by reviewer
        print('current reviewing paper from {}'.format(team.teammate))
        old_abstract = team.abstract
        prompt = Prompts.prompt_review_require_simple.replace("{paper}", old_abstract)
        mark_sum = 0
        team.paper_review==None
        for _ in range(self.reviewer_num):
            agent_prompt = format_msg(
                # prompt
                Msg(name="user", role="user", content=prompt),
            )
            reply = self.reviewer_pool[_].prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
            team.log_dialogue(self.reviewer_pool[_].name, reply.content)
            split_keywords = ['Overall']
            metric = extract_metrics(reply.content, split_keywords)
            if team.paper_review == None:
                team.paper_review = self.reviewer_pool[_].name+":\n"+reply.content
            else:
                team.paper_review = team.paper_review+"\n"+self.reviewer_pool[_].name+":\n"+reply.content
            for split_keyword in split_keywords:
                if metric[split_keyword] == None:
                    mark_sum = mark_sum + self.default_mark
                else:
                    mark_sum = mark_sum + metric[split_keyword]
        if mark_sum>=(5*self.reviewer_num):
            print('paper accept!!!!!!')
            team.state=self.over_state
            title = old_abstract.split("Abstract")[0]
            title = strip_non_letters(title.split("Title")[1])
            abstract = strip_non_letters(old_abstract.split("Abstract")[1])
            file_dict={}
            file_dict['title']=title
            file_dict['abstract']=abstract
            file_dict['id'] = len(self.paper_dicts)
            file_dict['authors'] = team.teammate
            file_dict['cite_papers'] = team.citation_id
            self.paper_dicts.append(file_dict)
            # add embedding into list
            embedding_list = []
            response = ollama.embeddings(model="mxbai-embed-large", prompt=abstract)
            embedding_list.append(response["embedding"])
            response = np.array(embedding_list)
            self.gpu_index.add(response)
        else:
            team.state = 5
        return team

    def id_to_agent(self, team_list):
        agent_list = []
        for agent_id in team_list:
            agent_list.append(self.id2agent[agent_id])
        return agent_list

    def agent_to_id(self, team_list):
        agent_list = []
        for agent_id in team_list:
            agent_list.append(agent_id.name)
        return agent_list

    def reference_paper(self, key_string, cite_number):
        query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=key_string)
        query_vector = np.array([query_vector['embedding']])
        D, I = self.gpu_index.search(query_vector, cite_number)

        paper_use = []
        for id in range(len(I[0])):
            paper_title = self.paper_dicts[I[0][id]]['title']
            paper_abstract = self.paper_dicts[I[0][id]]['abstract']
            paper_index = {}
            paper_index['title'] = paper_title
            paper_index['abstract'] = paper_abstract
            paper_use.append(paper_index)
        paper_reference = ""
        for id in range(len(paper_use)):
            paper_index = paper_use[id]
            paper_reference = paper_reference+"Paper {}:".format(id+1)+"\n"
            paper_reference = paper_reference+"Title: "+paper_index['title']+"\n"
            paper_reference = paper_reference+"Abstract: "+paper_index['abstract']+"}"+"\n"
        return paper_reference, I[0]

    def action_excution(self, value, epoch):
        action_dict = {
            2: self.select_topic,
            3: self.generate_idea,
            4: self.check_novelty,
            5: self.generate_abstract,
            6: self.generate_review
        }
        log_dict = {
            2: 'begin select topic',
            3: 'begin generate idea',
            4: 'begin check novelty',
            5: 'begin generate abstract',
            6: 'begin generate review'
        }
        if value>self.begin_state and value<self.over_state:
            print(f'Epoch{epoch}-------------------{log_dict[value]}')
        return action_dict.get(value, None)

    def running(self, epochs):
        # init team_pool
        print(f'Epoch{-1}-------------------initialize team')
        self.team_pool = self.select_coauthors()
        for epoch in range(epochs):
            # state 6 is an over
            # 1. generate paper review for state 6
            # 2. generate paper abstract for state 5
            # 3. generate idea for state 4
            # 4. check novelty for state 3
            # 5. select topics for state 2
            # 6. select coauthors for state 1
            for agent_index in range(len(self.team_pool)):
                for team_index in range(len(self.team_pool[agent_index])):
                    self.team_pool[agent_index][team_index].epoch = epoch
                    action = self.action_excution(self.team_pool[agent_index][team_index].state, epoch)
                    if action is not None:
                        self.team_pool[agent_index][team_index] = action(self.team_pool[agent_index][team_index])
                        if self.team_pool[agent_index][team_index].state == 7:
                            self.team_pool[agent_index][team_index].save_team_info()
                        print(f'Epoch{epoch}-------------------current action finished')
            print(f'Epoch{epoch}-------------------begin select authors')
            self.team_pool = self.select_coauthors()
            print(f'Epoch{epoch}-------------------current action finished')
        output_dir = "/home/bingxing2/ailab/scxlab0066/SocialScience/database/database.db"
        save2database(self.paper_dicts, output_dir)