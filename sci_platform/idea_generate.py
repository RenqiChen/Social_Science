import faiss
import ollama
import numpy as np
import os
import sqlite3
import json
from tqdm import tqdm
import sys
sys.path.append('../agentscope-main/src')
from scientist_utils import (
    extract_scientist_names,
    team_description,
    n2s,
    convert_you_to_other,
    team_description_detail,
    format_msg,
    read_txt_files_as_dict,
    extract_between_json_tags,
    extract_metrics,
    paper_search,
    strip_non_letters
)
from prompt import Prompts
# # topic
# topic = "Selected Topics: [Synthetic data sets for improving multimedia search and retrieval systems]"
# selected_topics = topic.split("Selected Topics:")[-1].strip()
# # find paper
# cpu_index = faiss.read_index("/home/bingxing2/ailab/group/ai4agr/crq/SciSci/faiss_index.index")  # 加载索引
# res = faiss.StandardGpuResources()  # 为 GPU 资源分配
# gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)  # 将索引移到 GPU
# query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=selected_topics)
# query_vector = np.array([query_vector['embedding']])
# D, I = gpu_index.search(query_vector, 5)
# print("Indices:", I)  # 打印索引

# def read_txt_files_as_dict(folder_path):
#     dict_list = []  # 用于存储所有文件的字典
    
#     # 遍历文件夹中所有的 .txt 文件
#     for filename in tqdm(os.listdir(folder_path)):
#         if filename.endswith(".txt"):  # 确保文件是 .txt 类型
#             file_path = os.path.join(folder_path, filename)
            
#             # 打开并读取每个 .txt 文件的内容
#             with open(file_path, 'r') as file:
#                 file_content = file.read()
#                 try:
#                     # 将内容解析为字典（假设内容是JSON格式）
#                     file_dict = eval(file_content)
#                 except json.JSONDecodeError:
#                     print(f"文件 {filename} 的内容不是有效的JSON格式，跳过该文件。")
#                     continue
                
#                 # 将字典添加到列表
#                 dict_list.append(file_dict)
#     return dict_list

# # 示例使用
# folder_path = "/home/bingxing2/ailab/group/ai4agr/crq/SciSci/papers"  # 替换为实际的文件夹路径
# all_dicts = read_txt_files_as_dict(folder_path)


# paper_use = []
# for id in range(len(I[0])):
#     paper_title = all_dicts[I[0][id]]['title']
#     paper_abstract = all_dicts[I[0][id]]['abstract']
#     paper_index = {}
#     paper_index['title'] = paper_title
#     paper_index['abstract'] = paper_abstract
#     paper_use.append(paper_index)
# paper_reference = ""
# for id in range(len(paper_use)):
#     paper_index = paper_use[id]
#     paper_reference = paper_reference+"Paper {}:".format(id+1)+"\n"
#     paper_reference = paper_reference+"Title: "+paper_index['title']+"\n"
#     paper_reference = paper_reference+"Abstract: "+paper_index['abstract']+"}"+"\n"
# print(len(paper_reference))
# prompt_existing_idea = "Here are the ideas that your team has already generated: '''{}'''\n".format(None)
# prompt_task = "Come up with the next impactful and creative idea for publishing a paper that will contribute significantly to the field."+"\n"
# prompt_topic = "When proposing your idea, please elaborate on the proposed topic: {}".format(selected_topics)+"\n"
# prompt_reference = "You may refer to these references: {}".format(paper_reference)+"\n"
# prompt_response = """
# "Please respond in the following format: 

# Thought: <THOUGHT> 

# New Idea: <IDEA>

# In <THOUGHT>, first briefly discuss your intuitions and motivations for the idea. 
# Detail your high-level plan, necessary design choices and ideal outcomes of the experiments. 
# Justify how the idea is different from the existing ones. 

# In <IDEA>, provide the new idea with the following fields: 
# - "Idea": A detailed description of the idea. 
# - "Title": A title for the idea, will be used for the report writing. 
# - "Experiment": An outline of the implementation. E.g. which functions need to be added or modified, how results will be obtained, ...
# - "Interestingness": A rating from 1 to 10 (lowest to highest).
# - "Feasibility": A rating from 1 to 10 (lowest to highest). 
# - "Novelty": A rating from 1 to 10 (lowest to highest). 

# Be cautious and realistic on your ratings. This JSON will be automatically parsed, so ensure the format is precise. You will have {num_reflections} rounds to iterate on the idea, but do not need to use them all.
# """
# prompt = prompt_task+prompt_topic+prompt_reference+prompt_response
# response = ollama.chat(model='llama3.1', messages=[
#   {
#     'role': 'user',
#     'content': prompt,
#   },
# ])

# prompt_abstract = """Based on the following research idea. Generate a concise and informative abstract for a scientific paper.""" 

# prompt_abstract_requirement = """The abstract should cover the following aspects:

# - "Introduction": Briefly introduce the research topic and its significance.
# - "Objective": Clearly state the main research question or hypothesis.
# - "Methods": Summarize the key methodologies used in the study.
# - "Results": Highlight the most important findings.
# - "Conclusion": Provide the primary conclusion and its implications.

# Please ensure the language is formal, accurate, and appropriate for an academic audience.
# """

# prompt_abstract_response = """The response format should be:

# ```json
# {
# Title: <TITLE>

# Abstract: <ABSTRACT>
# }
# ```
# This JSON will be automatically parsed, so ensure the format is precise.
# """
# print(response['message']['content'])

# prompt_research_idea = response['message']['content']

# prompt_abstract = prompt_abstract+"\n"+prompt_research_idea+"\n"+prompt_abstract_requirement+"\n"+prompt_abstract_response

# # idea generation
# response = ollama.chat(model='llama3.1', messages=[
#   {
#     'role': 'user',
#     'content': prompt_abstract,
#   },
# ])
# print(response['message']['content'])

# prompt_abstract_judgement = """
# Evaluate the following scientific paper abstract based on the following criteria:

# 1. **Clarity**: Is the abstract clear and easy to understand?
# 2. **Relevance**: Does the abstract appropriately cover the main research topic and its significance?
# 3. **Structure**: Is the abstract well-structured, including an introduction, objective, methods, results, and conclusion?
# 4. **Conciseness**: Is the abstract succinct without unnecessary details, yet comprehensive enough to summarize the key aspects of the research?
# 5. **Technical Accuracy**: Are the scientific terms and methodologies correctly presented and accurately described?
# 6. **Engagement**: Does the abstract engage the reader and encourage further reading of the full paper?
# 7. **Overall Score**: The overall rating of this paper.

# Provide a brief evaluation of each criterion by providing a rating from 1 to 10 (lowest to highest) and revise the abstract.

# **Original Abstract**: [Insert abstract here]
# """

# prompt_abstract_judgement = prompt_abstract_judgement.replace("[Insert abstract here]",response['message']['content'])

# prompt_abstract_revise_response = """The response format should be:

# **Revised Abstract**
# ```json
# Title: <TITLE>

# Abstract: <ABSTRACT>
# ```
# In <JSON>, provide the title and abstract. This JSON will be automatically parsed, so ensure the format is precise.
# """

# prompt_abstract_judgement = prompt_abstract_judgement+prompt_abstract_revise_response
# response = ollama.chat(model='llama3.1', messages=[
#   {
#     'role': 'user',
#     'content': prompt_abstract_judgement,
#   },
# ])

# print(response['message']['content'])
for _ in tqdm(range(100)):
    response = """
    ```json
    Title: 'anytime, anywhere: modal logics for mobile ambients', 

    Abstract: 'The Ambient Calculus is a process calculus where processes may reside within a hierarchy of locations and modify it. The purpose of the calculus is to study mobility, which is seen as the change of spatial configurations over time. In order to describe properties of mobile computations we devise a modal logic that can talk about space as well as time, and that has the Ambient Calculus as a model.'
    ```
    """

    old_abstract = extract_between_json_tags(response)
    title = old_abstract.split("Abstract")[0]
    title = title.split("Title:")[1].strip()
    related_papers = paper_search(title,top_k=5)
    max_iter = 2
    iter = 1
    while len(related_papers)==0:
        related_papers = paper_search(title)
        iter += 1
        print(iter)
        if iter > max_iter:
            break
    # print(len(related_papers))
    # print(related_papers)
    if len(related_papers)>0:
        abstract_check_prompt = Prompts.prompt_abstract_check.replace("[Insert your abstract here]", old_abstract)
        cite_abstract = ""
        word = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T']
        for paper_id in range(len(related_papers)):
            cite_abstract = cite_abstract+str(paper_id+1)+". Abstract {}: ".format(word[paper_id])+"Title: "+related_papers[paper_id]['title']+"\n"+"Abstract: "+related_papers[paper_id]['abstract']+"\n"
        abstract_check_prompt = abstract_check_prompt.replace("[Insert ref abstract here]", cite_abstract)
        abstract_check_prompt = abstract_check_prompt+"\n"+Prompts.prompt_response_check
        print(len(abstract_check_prompt))
    # abstract_check_prompt = Prompts.prompt_abstract_check.replace("[Insert your abstract here]", old_abstract)
    # abstract_check_prompt = abstract_check_prompt.replace("[Insert abstract A here]", "Title: "+related_papers[0]['title']+"\n"+"Abstract: "+related_papers[0]['abstract']+"\n")
    # abstract_check_prompt = abstract_check_prompt.replace("[Insert abstract B here]", "Title: "+related_papers[1]['title']+"\n"+"Abstract: "+related_papers[1]['abstract']+"\n")
    # abstract_check_prompt = abstract_check_prompt.replace("[Insert abstract C here]", "Title: "+related_papers[2]['title']+"\n"+"Abstract: "+related_papers[2]['abstract']+"\n")
    # abstract_check_prompt = abstract_check_prompt.replace("[Insert abstract D here]", "Title: "+related_papers[3]['title']+"\n"+"Abstract: "+related_papers[3]['abstract']+"\n")
    # abstract_check_prompt = abstract_check_prompt.replace("[Insert abstract E here]", "Title: "+related_papers[4]['title']+"\n"+"Abstract: "+related_papers[4]['abstract']+"\n")
    # abstract_check_prompt = abstract_check_prompt+"\n"+Prompts.prompt_response_check
    response = ollama.chat(model='llama3.1', messages=[
    {
        'role': 'user',
        'content': abstract_check_prompt,
    },
    ])
    print("abstract_check:")
    # comparison = extract_between_json_tags(response['message']['content'])
    # metric = extract_metrics(comparison, split_keywords=['Written Abstract vs A','Written Abstract vs B','Written Abstract vs C','Written Abstract vs D','Written Abstract vs E'])
    # print(metric)

    # prompt = Prompts.prompt_review_system+Prompts.prompt_review_require_simple.replace("{paper}", old_abstract)
    # print(len(prompt))
    # response = ollama.chat(model='llama3.1:70b', messages=[
    #   {
    #     'role': 'user',
    #     'content': prompt,
    #   },
    # ])
    print(len(response['message']['content']))

    # # 示例
    # text = "***   **123Hello, World!456::::   ***"
    # result = strip_non_letters(text)
    # print(result)  # 输出: Hello, World