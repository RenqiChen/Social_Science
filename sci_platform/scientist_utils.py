# -*- coding: utf-8 -*-
"""utils."""

import sys
sys.path.append('agentscope-main/src')
from agentscope.service import (
    dblp_search_publications,  # or google_search,
    arxiv_search
)
import re
from typing import Union, Any, Sequence

import numpy as np
from loguru import logger

from prompt import Prompts
from agentscope.agents import AgentBase
from agentscope.message import Msg
import os
from tqdm import tqdm
import json
import sqlite3

from concurrent.futures import ThreadPoolExecutor
from collections import Counter

def check_winning(alive_agents: list, wolf_agents: list, host: str) -> bool:
    """check which group wins"""
    if len(wolf_agents) * 2 >= len(alive_agents):
        msg = Msg(host, Prompts.to_all_wolf_win, role="assistant")
        logger.chat(msg)
        return True
    if alive_agents and not wolf_agents:
        msg = Msg(host, Prompts.to_all_village_win, role="assistant")
        logger.chat(msg)
        return True
    return False


def update_alive_players(
    survivors: Sequence[AgentBase],
    wolves: Sequence[AgentBase],
    dead_names: Union[str, list[str]],
) -> tuple[list, list]:
    """update the list of alive agents"""
    if not isinstance(dead_names, list):
        dead_names = [dead_names]
    return [_ for _ in survivors if _.name not in dead_names], [
        _ for _ in wolves if _.name not in dead_names
    ]


def majority_vote(votes: list) -> Any:
    """majority_vote function"""
    votes_valid = [item for item in votes if item != "Abstain"]
    # Count the votes excluding abstentions.
    unit, counts = np.unique(votes_valid, return_counts=True)
    return unit[np.argmax(counts)]


def extract_name_and_id(name: str) -> tuple[str, int]:
    """extract player name and id from a string"""
    try:
        name = re.search(r"\b[Pp]layer\d+\b", name).group(0)
        idx = int(re.search(r"[Pp]layer(\d+)", name).group(1)) - 1
    except AttributeError:
        # In case Player remains silent or speaks to abstain.
        logger.warning(f"vote: invalid name {name}, set to Abstain")
        name = "Abstain"
        idx = -1
    return name, idx


def extract_scientist_names(name: str) -> list:
    """extract player name and id from a string"""
    try:
        matches = re.findall(r"\b[Ss]cientist\d+\b", name)
        # idx = int(re.search(r"[Pp]layer(\d+)", name).group(1)) - 1
        names = [f"{num}" for num in matches]
    except AttributeError:
        # In case Player remains silent or speaks to abstain.
        logger.warning(f"vote: invalid name {name}, set to Abstain")
        names = ["Abstain"]
        idx = -1
    return list(set(names))


def n2s(agents: Sequence[Union[AgentBase, str]]) -> str:
    """combine agent names into a string, and use "and" to connect the last
    two names."""

    def _get_name(agent_: Union[AgentBase, str]) -> str:
        return agent_.name if isinstance(agent_, AgentBase) else agent_

    if len(agents) == 1:
        return _get_name(agents[0])

    return (
        ", ".join([_get_name(_) for _ in agents[:-1]])
        + " and "
        + _get_name(agents[-1])
    )

def team_description(team: list, over_state: int) -> str:
    """combine agent names into a string, and use "and" to connect the last
    two names."""
    output_string = "{"
    i = 1
    for team_index in team:
        if team_index.state != over_state:
            output_string += f"team{i}: {team_index.teammate}"
            i = i + 1
            if i < len(team):
                output_string += ", "
    output_string += "}"

    return output_string

def team_description_detail(team: list, agent_list: list, over_state: int) -> str:
    """combine agent names into a string, and use "and" to connect the last
    two names."""
    output_string = ""
    i=1
    for team_index in range(len(team)):
        if team[team_index].state!=over_state:
            team_list = team[team_index].teammate
            output_string += f"The Team{i} includes team members: {team_list}. "
            i=i+1
    output_string_before = f"You are currently a member of {i-1} teams. "
    # for agent in agent_list:
    #     if agent.name in independent_list:
    #         output_string += f"For {agent.name}, "
    #         output_string += convert_you_to_other(agent.sys_prompt)
    output_string = output_string_before + output_string + "Summarize the status of all the teams you are currently part of."
    return output_string

def convert_you_to_other(origin: str) -> str:
    after = origin.replace("Your", "His")
    after = after.replace("you", "he")
    after = after.replace("your", "his")
    return after


def set_parsers(
    agents: Union[AgentBase, list[AgentBase]],
    parser_name: str,
) -> None:
    """Add parser to agents"""
    if not isinstance(agents, list):
        agents = [agents]
    for agent in agents:
        agent.set_parser(parser_name)

# def  update_state(team: list, agent_index: int, state: int) -> list:
#     for team_index in team[agent_index]:
#         team_index['state'] = state
#     return team

def format_msg(*input: Union[Msg, Sequence[Msg]]) -> list:
    """Forward the input to the model.

    Args:
        args (`Union[Msg, Sequence[Msg]]`):
            The input arguments to be formatted, where each argument
            should be a `Msg` object, or a list of `Msg` objects.
            In distribution, placeholder is also allowed.

    Returns:
        `str`:
            The formatted string prompt.
    """
    input_msgs = []
    for _ in input:
        if _ is None:
            continue
        if isinstance(_, Msg):
            input_msgs.append(_)
        elif isinstance(_, list) and all(isinstance(__, Msg) for __ in _):
            input_msgs.extend(_)
        else:
            raise TypeError(
                f"The input should be a Msg object or a list "
                f"of Msg objects, got {type(_)}.",
            )

    return input_msgs

def paper_search(query : str,
                 top_k : int = 8,
                 start_year : int = None,
                 end_year : int = None,
                 search_engine : str = 'arxiv') -> list:
    """Given a query, retrieve k abstracts of similar papers from google scholar"""
    
    proxy = {
        'http':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
        'https':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
    }
    
    start_year = 0 if start_year is None else start_year
    end_year = 9999 if end_year is None else end_year
    papers = []
    if search_engine == 'google scholar':
        # retrieval_results = scholarly.search_pubs(query)
        retrieval_results = []
    elif search_engine == 'dblp':
        retrieval_results = dblp_search_publications(query, num_results = top_k)['content']
    else:
        temp_results = arxiv_search(query, max_results = top_k, proxy = proxy).content
        if isinstance(temp_results, dict):
            retrieval_results = temp_results['entries']
        else:
            retrieval_results = []
            print(temp_results)

    for paper in retrieval_results:

        if len(papers) >= top_k:
            break

        try:
            pub_year = paper.get('published', None)[:4]
        except:
            pub_year = paper.get('year', None)

        if pub_year and start_year <= int(pub_year) <= end_year:
            if search_engine == 'google scholar':
                paper_info = {
                    'title': paper.get('title'),
                    'authors': paper.get('authors'),
                    'year': pub_year,
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'venue': paper.get('venue')
                }
            elif search_engine == 'dblp':
                paper_info = {
                    'title': paper.get('title'),
                    'authors': paper.get('authors'),
                    'year': pub_year,
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'venue': paper.get('venue')
                }
            else:
                paper_info = {
                    'title': paper.get('title'),
                    'authors': ','.join(paper.get('authors')),
                    'year': pub_year,
                    'abstract': paper.get('summary'),
                    'pdf_url': paper.get('url'),
                    'venue': paper.get('comment')
                }

            # print(paper_info)
            papers.append(paper_info)

    return papers

# def process_file(file_path, id):
#     try:
#         print(id)
#         with open(file_path, 'r') as file:
#             file_content = file.read()
#             file_dict_old = eval(file_content)
#             file_dict = {
#                 'title': file_dict_old.get('title'),
#                 'abstract': file_dict_old.get('abstract'),
#                 'id': id,
#                 'authors': None,
#                 'cite_papers': None
#             }
#             return file_dict
#     except json.JSONDecodeError:
#         print(f"文件 {file_path} 的内容不是有效的JSON格式，跳过该文件。")
#         return None

# def read_txt_files_as_dict(folder_path):
#     dict_list = []
#     id = 0
#     with ThreadPoolExecutor() as executor:
#         # 只处理 .txt 文件
#         txt_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")]
        
#         # 并行处理文件
#         results = list(tqdm(executor.map(lambda file: process_file(file, id), txt_files), total=len(txt_files)))

#         # 过滤掉 None 结果
#         dict_list = [res for res in results if res is not None]
        
#     return dict_list

def read_txt_files_as_dict(folder_path):
    dict_list = []  # 用于存储所有文件的字典
    id = 0
    # 遍历文件夹中所有的 .txt 文件
    for filename in tqdm(os.listdir(folder_path)):
        if filename.endswith(".txt"):  # 确保文件是 .txt 类型
            file_path = os.path.join(folder_path, filename)
            
            # 打开并读取每个 .txt 文件的内容
            with open(file_path, 'r') as file:
                file_content = file.read()
                try:
                    # 将内容解析为字典（假设内容是JSON格式）
                    file_dict_old = eval(file_content)
                    file_dict={}
                    file_dict['title']=file_dict_old['title']
                    file_dict['abstract']=file_dict_old['abstract']
                    file_dict['id'] = id
                    file_dict['authors'] = None
                    file_dict['cite_papers'] = None
                except json.JSONDecodeError:
                    print(f"文件 {filename} 的内容不是有效的JSON格式，跳过该文件。")
                    continue
                
                # 将字典添加到列表
                dict_list.append(file_dict)
                id = id + 1
    return dict_list

def extract_between_json_tags(text, num=None):
    json_blocks = re.findall(r'```json(.*?)```', text, re.DOTALL)
    
    if not json_blocks:
        start_tag = '```json'
        end_tag = '```'
        start_idx = text.find(start_tag)
        end_idx = text.find(end_tag, start_idx + len(start_tag))
        return text[start_idx + len(start_tag):].strip()
    else:
        if num==None:
            combined_json = ''.join(block.strip() for block in json_blocks)
        else:
            combined_json = ''.join(block.strip() for block in json_blocks[:num])
        return combined_json
    

def extract_metrics(text, split_keywords):
    # 存储每个指标及其数值
    metrics = {}
    
    for keyword in split_keywords:
        # 使用关键词进行分割
        parts = text.split(keyword)
        if len(parts) > 1:
            # 在分割后的部分中找到第一个数字
            match = re.search(r'\d+', parts[1])
            if match:
                value = int(match.group())
                metrics[keyword.strip('"')] = value
            else:
                metrics[keyword.strip('"')] = None
        else:
            metrics[keyword.strip('"')] = None
    
    return metrics

def strip_non_letters(text):
    # 正则表达式匹配非字母字符并移除它们
    return re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', text)

def save2database(paper_list : list[dict], output_dir : str):
    # connect to database, if it exists then delete it
    if os.path.isfile(output_dir):
        os.remove(output_dir)
    conn = sqlite3.connect(output_dir)
    # create cursor
    cursor = conn.cursor()

    # create table
    print('build paper table...')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY,
                title TEXT,
                authors TEXT,
                cite_papers TEXT,
                abstract TEXT
            )
        ''')

    for paper in paper_list:
        id = int(paper['id'])
        title = paper['title']
        abstract = paper['abstract']
        if paper['authors']!=None:
            authors = ';'.join(paper['authors'])
            paper_references = ';'.join(map(str, paper['cite_papers']))
        else:
            authors = None
            paper_references = None

        # Define your user data (id, name, affiliation)
        paper_data = (id,
                      title,
                      authors,
                      paper_references,
                      abstract)

        # Insert query
        query = '''
            INSERT INTO papers (id, title, authors, cite_papers, abstract)
            VALUES (?, ?, ?, ?, ?)
            '''

        # Execute the query with user data
        cursor.execute(query, paper_data)

    conn.commit()
    cursor.close()
    conn.close()

def count_team(team_list: list[dict], over_state: int):
    num = 0
    for team in team_list:
        if team.state<over_state:
            num = num+1
    return num


def top_three_indices(lst):
    # 使用enumerate获取元素及其索引，并根据元素值进行排序
    sorted_indices = sorted(enumerate(lst), key=lambda x: x[1], reverse=True)
    
    # 取出前三大的元素的索引
    top_three = [index for index, value in sorted_indices[:3]]
    
    return top_three

def extract_first_number(s):
    # 使用正则表达式查找字符串中的第一个数字
    match = re.search(r'\d+', s)
    if match:
        return match.group()  # 返回匹配到的第一个数字
    return None  # 如果没有找到数字，返回 None


def most_frequent_element(arr):
    # 使用 Counter 计算每个元素的出现次数
    count = Counter(arr)
    
    # 返回出现次数最多的元素
    most_common_element = count.most_common(1)[0][0]
    
    return most_common_element
