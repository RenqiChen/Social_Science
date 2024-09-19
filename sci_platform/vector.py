import numpy as np
import faiss
import sys
sys.path.append('../agentscope-main/src')
from agentscope.manager import ModelManager
import ollama
from tqdm import tqdm
import os
import json
def read_txt_files_as_dict(folder_path):
    dict_list = []  # 用于存储所有文件的字典
    
    # 遍历文件夹中所有的 .txt 文件
    for filename in tqdm(os.listdir(folder_path)):
        if filename.endswith(".txt"):  # 确保文件是 .txt 类型
            file_path = os.path.join(folder_path, filename)
            
            # 打开并读取每个 .txt 文件的内容
            with open(file_path, 'r') as file:
                file_content = file.read()
                try:
                    # 将内容解析为字典（假设内容是JSON格式）
                    file_dict = eval(file_content)
                except json.JSONDecodeError:
                    print(f"文件 {filename} 的内容不是有效的JSON格式，跳过该文件。")
                    continue
                
                # 将字典添加到列表
                dict_list.append(file_dict)
    return dict_list

# 示例使用
folder_path = "/home/bingxing2/ailab/scxlab0066/SocialScience/papers_simple"  # 替换为实际的文件夹路径
all_dicts = read_txt_files_as_dict(folder_path)

print(len(all_dicts))
# 假设你有一个特定的 Ollama 嵌入模型，如 'ollama-mebedding'
embedding_list = []
client = ollama.Client()
for i in tqdm(range(len(all_dicts))):
    t = all_dicts[i]['abstract']
    response = ollama.embeddings(model="mxbai-embed-large", prompt=t)
    embedding_list.append(response["embedding"])
    if i==0:
        print(t)
# embedding_list= []
# embedding_list.append(np.random.rand(1024))
response = np.array(embedding_list)
res = faiss.StandardGpuResources()  # 为 GPU 资源分配
index = faiss.IndexFlatL2(1024)
gpu_index = faiss.index_cpu_to_gpu(res, 0, index)  # 将索引移到 GPU
print(response.shape)
gpu_index.add(response)  # 添加数据

print(gpu_index.ntotal)  # 输出索引中的向量总数

# nq = 5  # 查询向量的数量
# xq = np.random.random((nq, d)).astype('float32')  # 生成一些查询向量

# k = 4  # 想要返回的最近邻个数
# D, I = index.search(xq, k)  # 进行搜索
# # D 是距离，I 是对应的向量索引
# print("Distances:", D)
# print("Indices:", I)
# 将 GPU 索引转换为 CPU 索引
cpu_index = faiss.index_gpu_to_cpu(gpu_index)

# 保存 CPU 索引到文件
faiss.write_index(cpu_index, "faiss_index_21370.index")

cpu_index = faiss.read_index("faiss_index_21370.index")  # 加载索引
print(cpu_index.ntotal)
