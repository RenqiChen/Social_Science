import re

llama3_8b_ollama_model_configuration = [
    {
        "config_name": "my_ollama_chat_config",
        "model_type": "ollama_chat",
        "model_name": "llama3:70b",
        "options": {
            "temperature": 0.5,
            "seed": 123
        },
        "keep_alive": "5m"
    },
    # {
    #     "config_name": "my_ollama_generate_config",
    #     "model_type": "ollama_generate",
    #     "model_name": "llama3",
    #     "options": {
    #         "temperature": 0.5,
    #         "seed": 123
    #     },
    #     "keep_alive": "5m"
    # },
    {
        "config_name": "my_ollama_embedding_config",
        "model_type": "ollama_embedding",
        "model_name": "llama3:70b",
        "options": {
            "temperature": 0.5,
            "seed": 123
        },
        "keep_alive": "5m"
    },
    # {
    #     "config_name": "ollama_llama3_70b",
    #     "model_type": "ollama_chat",
    #     "model_name": "llama3:70b",
    #     "options": {
    #         "temperature": 0.5,
    #         "seed": 123
    #     },
    #     "keep_alive": "5m"
    # }
]

# import ollama
# response = ollama.chat(model='llama3', messages=[
#     {
#         'role': 'assistant',
#         'content': 'Why is the sky blue?',
#     },
# ])
#
# print(response)

import sys
sys.path.append('src')
import agentscope
from agentscope.message import Msg
from agentscope.agents import UserAgent, DialogAgent, LlamaIndexAgent, ReActAgent
from agentscope.rag import KnowledgeBank
from agentscope.msghub import msghub
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

# def write_out_response(name: str, response: str, dir: str):
#     """Given agent name, response and output direction, write agent response to a txt file
#
#     Args:
#         name (str): agent name
#         response (str): agent response
#         dir (str): output file direction
#     """
#
#     if os.path.exists(dir)==False:
#         os.mkdir(dir)
#
#     with open(dir, 'a') as file:
#         file.write('{}: {} \n'.format(name, response))
#
#     status = ServiceExecStatus.SUCCESS
#     return ServiceResponse(status, 'Successfully write out responses!')

agentscope.init(model_configs=llama3_8b_ollama_model_configuration)

# knowledge
knowledge_bank = KnowledgeBank("../papers/knowledge_config.json")
# knowledge_bank.add_data_as_knowledge(
#     knowledge_id="professor_papers",
#     emb_model_name="ollama_llama3_8b",
#     data_dirs_and_types={
#         "../papers": [".pdf"],
#     },
# )
knowledge = knowledge_bank.get_knowledge("professor_papers")

# user agent
user = UserAgent("user")

# # rag agent
# agent1 = LlamaIndexAgent(
#     name="Sam",
#     sys_prompt="You're a helpful AI professor who is working on conversational recommendation, Tom is your "
#                "student, you are enthusiastic on answering any question from him.",
#     model_config_name="my_ollama_chat_config",
#     knowledge_list=[knowledge], # provide knowledge object directly
#     similarity_top_k=2,
#     log_retrieval=False,
#     recent_n_mem_for_retrieve=3,
# )

# toolkit
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

# react agent
mentor_agent = ReActAgent(
    name="Tom",
    model_config_name="my_ollama_chat_config",
    sys_prompt="Your name is Tom, and you are a very helpful research assistant. "
               "Your job is to assist the user in completing various tasks. "
               "You are the mentor of Sam. If Sam gets any problems during finishing the job, you need to discuss with him and give a solution.",
    verbose=True,
    service_toolkit=service_toolkit,
    max_iters=5,
)

student_agent = ReActAgent(
    name="Sam",
    model_config_name="my_ollama_chat_config",
    sys_prompt="Your name is Sam, and you are a very helpful research assistant. "
               "Your job is to assist the user in completing various tasks."
               "You mentor is Tom, After getting a task from user, you need to complete the job."
               "If you get any troubles during finishing the job, you need to discuss with Tom by @Tom and find a solution.",
    verbose=True,
    service_toolkit=service_toolkit,
    max_iters=5,
)

agent_pool = [student_agent, mentor_agent]
# start_time = time.time()

DEFAULT_TOPIC = """
    This is a chat room and you can speak freely and briefly.
    """
SYS_PROMPT = """
    You can designate a member to reply to your message, you can use the @ symbol.
    This means including the @ symbol in your message, followed by
    that person's name, and leaving a space after the name.
    All participants are: {agent_names}
    """

hint = Msg(
    name="Host",
    content=DEFAULT_TOPIC
            + SYS_PROMPT.format(
        agent_names=[agent.name for agent in agent_pool],
    ),
)

total_start_time = time.time()
# Initialize MsgHub with participating agents
speak_list = [student_agent]
with msghub(participants=agent_pool, announcement=hint) as hub:
    x = None
    while True:
        # user turn
        x = user(x)
        if x.content == "exit":
            break
        elif x.content == "":
            pass
        else:
            target_agents = filter_agents(x.content, agent_pool)
            hub.broadcast(x)
        speak_list = target_agents + speak_list

        if len(speak_list) > 0:
            next_agent = speak_list.pop(0)
            x = next_agent()
            target_agents = filter_agents(x.content['speak'], agent_pool)
            speak_list = target_agents + speak_list

test_case1 = "Find lecun's recent 5 papers, and output what you got to a json file"
# end_time = time.time()
# execution_time = end_time - start_time
# print("程序运行时间为：", execution_time, "秒")