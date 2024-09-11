from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader(
    # input_files=['./data/ch.txt']
    input_files=['./output.txt']
).load_data()

splitter = SentenceSplitter.from_defaults()

nodes = splitter.get_nodes_from_documents(documents)

text_list = []
for i, node in enumerate(nodes):
    text_list.append(node.text)
print(len(text_list))