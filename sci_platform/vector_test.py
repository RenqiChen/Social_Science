import faiss
import numpy as np
import faiss
import ollama
cpu_index = faiss.read_index("faiss_index.index")  # 加载索引

# 创建查询向量
query_txt = "The Ambient Calculus is a process calculus where processes may reside within a hierarchy of locations and modify it. "
"The purpose of the calculus is to study mobility, "
"which is seen as the change of spatial configurations over time. "
"In order to describe properties of mobile computations we devise a modal logic that can talk about space as well as time, "
"and that has the Ambient Calculus as a model."

query_txt_2 = "The Ambient Calculus is a process calculus where processes may reside within a hierarchy of locations and modify it. The purpose of the calculus is to study mobility, which is seen as the change of spatial configurations over time. In order to describe properties of mobile computations we devise a modal logic that can talk about space as well as time, and that has the Ambient Calculus as a model."

query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=query_txt)
query_vector = np.array([query_vector['embedding']])
print(query_vector)
print(query_vector.shape)

query_vector_2 = ollama.embeddings(model="mxbai-embed-large", prompt=query_txt_2)
query_vector_2 = np.array([query_vector_2['embedding']])
print(query_vector_2)
# 搜索最接近的 4 个向量
cpu_index.add(query_vector_2)

D, I = cpu_index.search(query_vector, 10)

# 输出结果
print("Indices:", I)  # 打印索引
print("Distances:", D)  # 打印距离
