import re
import sys
sys.path.append('src')
import agentscope
from agentscope.message import Msg
from agentscope.agents import UserAgent, DialogAgent, LlamaIndexAgent, ReActAgent
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
from agentscope.models import load_model_by_config_name
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
import time
import os.path
from agentscope.service import (
    bing_search,  # or google_search,
    read_text_file,
    write_text_file,
    ServiceToolkit,
    ServiceResponse,
    ServiceExecStatus,
    dblp_search_authors,
    dblp_search_publications,
    read_json_file,
    write_json_file
)

from react_test import retrieve_from_list

def filter_agents(string: str, agents: list):
    """
    该函数会筛选输入字符串中以'@'为前缀的给定名称的出现，并返回找到的名称列表。
    """
    if len(agents) == 0:
        return []
    print('content: ', string)
    # 创建一个匹配@后跟任何候选名字的模式
    pattern = (
            r"@(" + "|".join(re.escape(agent.name) for agent in agents) + r")\b"
    )
    print('pattern: ', pattern)
    # 在字符串中找到所有模式的出现
    matches = re.findall(pattern, string)
    print('matches: ', matches)
    # 为了快速查找，创建一个将代理名映射到代理对象的字典
    agent_dict = {agent.name: agent for agent in agents}
    # 返回匹配的代理对象列表，保持顺序
    ordered_agents = [
        agent_dict[name] for name in matches if name in agent_dict
    ]
    return ordered_agents

# tools
def sum_num(a: float, b: float) -> float:
    """Add two floating point numbers and returns the result floating point number

    Args:
        a (float): argument1
        b (float): argument2

    Returns:
        float: result
    """
    output = a + b
    status = ServiceExecStatus.SUCCESS
    return ServiceResponse(status, output)


def multiply_num(a: float, b: float) -> float:
    """Multiply two floating point number and returns the result floating point number

    Args:
        a (float): argument1
        b (float): argument2

    Returns:
        float: result
    """
    output = a * b
    status = ServiceExecStatus.SUCCESS
    return ServiceResponse(status, output)

def convert_list2dict(data_name:str, data_list:list) -> dict:
    """Convert a list to dict

    Args:
        data_name (str): name of input data
        data_list (list): input data list

    Returns:
        result (dict): a dictionary containing data_list
    """
    output = {
        data_name:data_list
    }
    status = ServiceExecStatus.SUCCESS
    return ServiceResponse(status, output)

agentscope.init(model_configs="./configs/model_configs.json",)

user = UserAgent("user")

service_toolkit = ServiceToolkit()
tool_list = [
    read_text_file,
    write_text_file,
    dblp_search_authors,
    dblp_search_publications,
    read_json_file,
    write_json_file,
    sum_num,
    multiply_num,
    convert_list2dict
]

for tool in tool_list:
    service_toolkit.add(tool)
emb_model_name = "ollama_embedding-qwen:0.5b"
emb_model=load_model_by_config_name(emb_model_name)

documents = SimpleDirectoryReader(input_files=['/home/bingxing2/ailab/scxlab0066/SciSci/Agentscope/agentscope-main/ours/agent_test/books/output.txt']).load_data()

splitter = SentenceSplitter(chunk_size=4096, chunk_overlap=20)

nodes = splitter.get_nodes_from_documents(documents)

text_list = []

for i, node in enumerate(nodes):
    text_list.append(node.text)

print(len(text_list))
service_toolkit.add(retrieve_from_list, knowledge = text_list, top_k=2, embedding_model = emb_model)
service_toolkit.remove(retrieve_from_list)
service_toolkit.add(retrieve_from_list, knowledge = text_list, top_k=2, embedding_model = emb_model)
print('true')
# print(retrieve_from_list({'query':'parallel branch'},knowledge=text_list, embedding_model=emb_model))