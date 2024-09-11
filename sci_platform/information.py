import sys
sys.path.append('../agentscope-main/src')
import os
import agentscope
from agentscope.rag import KnowledgeBank
from agentscope.agents import SciAgent
import numpy as np
import json
from prompt import Prompts

from functools import partial
from scientist_utils import (
    extract_scientist_names,
    team_description,
    n2s,
    set_parsers,
)
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline


class Platform:
    r"""Platform."""

    def __init__(self,
                 model_configuration: str = './configs/model_configs.json',
                 agent_num: int = 156,
                 root_dir: str = '/home/bingxing2/ailab/group/ai4agr/shy/s4s',
                 paper_info_dir: str = 'papers',
                 author_info_dir: str = 'authors',
                 adjacency_matrix_dir: str = '156authors_degree_ge50_from_year2000to2010',
                 agent_model_config_name: str = 'ollama_llama3_8b',
                 knowledgeBank_config_dir: str = "./configs/knowledge_config.json",
                 hop_num: int = 2,
                 group_max_discuss_iteration: int = 1,
                 recent_n_team_mem_for_retrieve: int = 1
                 ):
        self.agent_num = agent_num
        self.paper_info_dir = os.path.join(root_dir, paper_info_dir)
        self.author_info_dir = os.path.join(root_dir, author_info_dir)
        self.adjacency_matrix_dir = os.path.join(root_dir, adjacency_matrix_dir)
        
        # author2paper file: dict{'authorID':[paperID1, paperID2, ...]}
        with open('{}/author2paper.json'.format(root_dir), 'r') as file:
            self.author2paper = json.load(file)

        # load k-hop adjacency matrix
        self.degree_int2word = ['one', 'two', 'three', 'four', 'five']
        self.adjacency_matrix = np.loadtxt(
            '{}/adj_matrix.txt'.format(self.adjacency_matrix_dir), dtype=int)

        # check if agent_num is valid
        if self.agent_num is None:
            self.agent_num = len(self.adjacency_matrix)
        else:
            assert self.agent_num <= len(self.adjacency_matrix)

        # load agentID2authorID file: dict{'agentID': 'authorID'}
        with open('{}/agentID2authorID.json'.format(self.adjacency_matrix_dir), 'r') as file:
            self.agentID2authorID = json.load(file)
        
        # init agent pool
        self.agent_pool = [self.init_agent(str(agent_id), agent_model_config_name, self.adjacency_matrix) for agent_id in range(self.agent_num)]

        for i, element in enumerate(self.agent_pool):
            # 生成文件名，可以使用索引i或其他命名方式
            filename = f"./books/author_{i}.txt"
    
            # 打开文件并写入元素内容
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(element)
        

    def init_agent(self, agent_id, agent_model_config_name, adjacency_matrix):
        # load author info
        with open('{}/{}.json'.format(self.author_info_dir, self.agentID2authorID[agent_id]), 'r') as file:
            author_info = json.load(file)

        author_id = author_info['author_id']
        author_name = author_info['author_name']
        author_affiliations = author_info['author_affiliations']
        research_topics = str(author_info['research_topics'])
        paper_count = author_info['paper_count']
        citation_number = author_info['citation_number']
        connection = adjacency_matrix[int(agent_id)]
        connection = ['Scientist{}'.format(index) for index, value in enumerate(connection) if value != 0]

        author_affiliations_new = []
        for string in author_affiliations:
            print(string)
            list_index = string.split(',')
            print(list_index)
            if len(list_index)>2:
                list_index = list_index[:-2]
            string_index = ','.join(list_index)
            author_affiliations_new.append(string_index)
        author_affiliations_new = list(set(author_affiliations_new))[:3]
        
        # prompt
        prompt = 'Your name is Scientist{}, ' \
                 'you belong to following affiliations {}, ' \
                 'you have researched on following topics {}, ' \
                 'you have published {} papers, ' \
                 'you have {} citations, '\
                 'you have previously collaborated with these individuals {}.'.format(agent_id, 
                                               author_affiliations_new, 
                                               research_topics,
                                               paper_count,
                                               citation_number,
                                               connection)
        return prompt

plat = Platform()

