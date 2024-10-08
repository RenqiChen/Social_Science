import sys
import os
import numpy as np
import json
import re
import ollama
from functools import partial
import faiss

sys.path.append('../agentscope-main/src')
import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.agents import SciAgent
from agentscope.message import Msg

from sci_team.SciTeam import Team
from utils.prompt import Prompts
from utils.scientist_utils import (
    team_description,
    convert_you_to_other,
    team_description_detail,
    read_txt_files_as_dict,
    extract_between_json_tags,
    count_team,
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

            for leader_index in range(len(self.team_pool)):
                for team_index in range(len(self.team_pool[leader_index])):
                    self.team_pool[leader_index][team_index].epoch = epoch
                    self.team_pool[leader_index][team_index].action_excution(self)
                    if self.team_pool[leader_index][team_index].state == 7:
                        self.team_pool[leader_index][team_index].save_team_info()

            print(f'Epoch{epoch}-------------------begin select authors')
            self.team_pool = self.select_coauthors()
            print(f'Epoch{epoch}-------------------current action finished')