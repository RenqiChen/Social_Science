# -*- coding: utf-8 -*-
"""utils."""

from loguru import logger
from tqdm import tqdm
from collections import Counter
from typing import Union, Any, Sequence
import numpy as np
import json
import sqlite3
import re
import os
import sys

sys.path.append('agentscope-main/src')
from agentscope.service import (
    dblp_search_publications,  # or google_search,
    arxiv_search
)
from agentscope.agents import AgentBase
from agentscope.message import Msg

from utils.prompt import Prompts

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

def formated_msg2str(input):
    input_strs = []
    for msg in input:
        input_strs.append(msg.name + ':' + msg.content)
    return '\n'.join(input_strs)

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
                url = paper.get('entry_id')
                # Regular expression to extract arXiv ID
                pattern = r'arxiv\.org\/abs\/([0-9]+\.[0-9]+)'

                # Find the arXiv ID
                match = re.search(pattern, url)
                arxiv_id = match.group(1)

                paper_info = {
                    'title': paper.get('title'),
                    'authors': ','.join(paper.get('authors')),
                    'year': pub_year,
                    'abstract': paper.get('summary'),
                    'pdf_url': paper.get('url'),
                    'venue': paper.get('comment'),
                    'arxiv_id': arxiv_id
                }

            # print(paper_info)
            papers.append(paper_info)

    return papers

def read_txt_files_as_dict(folder_path):
    dict_list = []  
    id = 0
    for filename in tqdm(os.listdir(folder_path)):
        if filename.endswith(".txt"):  
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r') as file:
                file_content = file.read()
                try:
                    file_dict_old = eval(file_content)
                    file_dict={}
                    file_dict['title']=file_dict_old['title']
                    file_dict['abstract']=file_dict_old['abstract']
                    file_dict['year']=file_dict_old['year']
                    file_dict['citation']=file_dict_old['citation']
                    file_dict['id'] = id
                    file_dict['authors'] = None
                    file_dict['cite_papers'] = None
                except json.JSONDecodeError:
                    print(f"File {filename} is not JSON format. Ignore and continue.")
                    continue

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

    metrics = {}

    for keyword in split_keywords:

        parts = text.split(keyword)
        if len(parts) > 1:

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

    sorted_indices = sorted(enumerate(lst), key=lambda x: x[1], reverse=True)


    top_three = [index for index, value in sorted_indices[:3]]

    return top_three

def extract_first_number(s):

    match = re.search(r'\d+', s)
    if match:
        return match.group()  
    return None  


def most_frequent_element(arr):

    count = Counter(arr)

    most_common_element = count.most_common(1)[0][0]

    return most_common_element
