import sqlite3
import os
import json
from community import community_louvain
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import networkx as nx
from tqdm import tqdm
# import cugraph as cnx

def community_visualization(G, data_save_dir = None, draw_edge = False):
    if data_save_dir is None:
        partition = community_louvain.best_partition(G)
    else:
        community_dir = os.path.join(data_save_dir, 'community_partition.json')
        if os.path.exists(community_dir):
            print('load generated communities...')
            with open(community_dir, 'r') as file:
                partition = json.load(file)
        else:
            # compute the best partition
            print('start generating communities...')
            partition = community_louvain.best_partition(G)
            # partition, _ = cugraph.louvain(G)
            with open(community_dir, 'w') as file:
                json.dump(partition, file, indent=4)

    # node degree
    # Calculate node degrees
    degree_dict = dict(G.degree())
    # Map degrees to node sizes (you can scale the size for better visibility)
    node_sizes = [v for v in degree_dict.values()]
    max_size = max(node_sizes)
    min_size = min(node_sizes)
    node_sizes = [int(v / (max_size - min_size) * 50) + 1 for v in node_sizes]

    # draw the graph
    print('start drawing...')
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, k=0.1, seed=1024)
    # color the nodes according to their partition
    cmap = plt.get_cmap('viridis', max(partition.values()) + 1)
    nx.draw_networkx_nodes(G, pos, partition.keys(),
                           node_size=node_sizes,
                           cmap=cmap,
                           node_color=list(partition.values()))
    if draw_edge:
        nx.draw_networkx_edges(G, pos, alpha=0.5)

    img_save_dir = 'results'
    if not os.path.exists(img_save_dir):
        os.mkdir(img_save_dir)
    plt.savefig(os.path.join(img_save_dir, 'cluster_community.png'), bbox_inches='tight')
    # plt.show()

def load_paper_reference(paperIDs, root_dir):
    print('load references...')
    # load database
    database_dir = os.path.join(root_dir, 'global_database.db')
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()
    # load refs
    paper_references = []
    for paperID in tqdm(paperIDs):
        cursor.execute(f'SELECT paper_references FROM papers WHERE id = {paperID}')
        rows = cursor.fetchall()
        paper_references.append(set(rows[0][0].split(';')) if rows[0][0] is not None else rows[0][0])
    return paper_references

def build_co_citing_net(root_dir, used_data_dir, start_year, end_year):
    # graph_dir = os.path.join(used_data_dir, 'co_citing_network.gml')
    # # load graph if exists
    # if os.path.exists(graph_dir):
    #     print('load co-citing graph...')
    #     G = nx.read_gml(graph_dir)
    #     return G

    # extract valid papers
    valid_papers = extract_valid_papers(root_dir, used_data_dir, start_year, end_year)
    print(f'there are {len(valid_papers)} papers published...')

    # extract paper refs
    paper_references = load_paper_reference(valid_papers, root_dir)

    # build co-citing network
    print("build co-citing network...")
    # init graph
    G = nx.Graph()
    for i in range(len(valid_papers)):
        G.add_node(i)
    # add edges
    for i in tqdm(range(len(paper_references))):
        paper_i_reference = paper_references[i]

        if paper_i_reference is None:
            continue
        for j in range(i+1, len(paper_references)):
            paper_j_reference = paper_references[j]
            if paper_j_reference is None or G.has_edge(i, j):
                continue
            for ref in paper_i_reference:
                if ref in paper_j_reference:
                    G.add_edge(i, j)
                    G.add_edge(j, i)
                    break
    # nx.write_gml(G, graph_dir)

    # remove low degree nodes
    low_degree_node = [x for x in G.nodes() if G.degree(x) < min(10, (len(valid_papers) // 1000))]
    G.remove_nodes_from(low_degree_node)
    return G

def extract_valid_papers(root_dir, used_data_dir, start_year, end_year):
    print("extract all valid papers...")
    # load database
    database_dir = os.path.join(root_dir, 'global_database.db')
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()

    # extract all valid papers
    cursor.execute(f'SELECT * FROM papers WHERE year >= {start_year} AND year <= {end_year}')
    rows = cursor.fetchall()

    # load author2paper
    with open('{}/author2paper.json'.format(root_dir), 'r') as file:
        author2paper = json.load(file)
    # load authors
    with open('{}/agentID2authorID.json'.format(os.path.join(root_dir, used_data_dir)), 'r') as file:
        agentID2authorID = json.load(file)

    all_papers = []
    for agentID, authorID in agentID2authorID.items():
        try:
            all_papers.extend(author2paper[authorID])
        except:
            pass

    all_papers = set(all_papers)

    valid_papers = []
    for row in rows:
        paper_id = row[0]
        paper_abstract = row[-1]

        if paper_abstract is None or str(paper_id) not in all_papers:
            continue
        print(paper_abstract)
        valid_papers.append(paper_id)
    return valid_papers

if __name__ == '__main__':
    # load the karate club graph
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    used_data_dir = 'authors_degree_ge50_from_year2000to2010'
    start_year = 2000
    end_year = 2010
    G = build_co_citing_net(root_dir, used_data_dir, start_year, end_year)
    # community_visualization(G, os.path.join(root_dir, used_data_dir))
    community_visualization(G)

    