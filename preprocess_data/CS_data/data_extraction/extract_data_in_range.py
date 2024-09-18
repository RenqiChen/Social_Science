import json
import re
from tqdm import tqdm
import os
import numpy as np
import sqlite3

log_list = []

def extract_authors(root_dir, start_time, end_time):
    # load database
    global_database_name = 'global_database.db'
    global_conn = sqlite3.connect(os.path.join(root_dir, global_database_name))
    global_cursor = global_conn.cursor()

    # load paper2author
    with open('{}/paper2author.json'.format(root_dir), 'r') as file:
        paper2author = json.load(file)

    # load all papers
    global_cursor.execute(f"SELECT id FROM papers WHERE year >= {start_time} AND year <= {end_time}")
    paper_list = global_cursor.fetchall()

    author_list = []
    valid_paper_num = 0

    for paper in tqdm(paper_list):
        paper_id = str(paper[0])

        try:
            author_list.extend(paper2author[paper_id])
            valid_paper_num+=1
        except:
            pass

    log_text = "{} of {} papers are valid".format(valid_paper_num, len(paper_list))
    log_list.append(log_text)
    print(log_text)

    log_text = 'There are {} authors involved from year {} to {}'.format(len(author_list), start_time, end_time)
    log_list.append(log_text)
    print(log_text)

    global_cursor.close()
    global_conn.close()

    return list(set(author_list))

def extract_valid_authors(authors, min_degree = 2, min_paper = 50):
    with open('{}/author2coauthor.json'.format(root_dir), 'r') as file:
        author2coauthor = json.load(file)

    with open('{}/author2paper.json'.format(root_dir), 'r') as file:
        author2paper = json.load(file)

    # first phase filtering
    filtered_authors = []
    author_set = set(authors)
    for authorID in tqdm(authors):
        # for each author check whether he can be found in author2coauthor file
        if authorID in author2coauthor.keys():
            degree = 0
            for coauthor in author2coauthor[authorID]:
                # for each coauthor check whether he can be found in author2coauthor file and valid_authors list
                if len(author2paper[coauthor['coauthor_id']]) >= min_paper \
                        and coauthor['coauthor_id'] in author_set \
                        and coauthor['coauthor_id'] in author2coauthor.keys():
                    degree += 1
            if degree >= min_degree:
                filtered_authors.append(authorID)

    # second phase filtering
    valid_authors = []
    filtered_authors_set = set(filtered_authors)
    for authorID in tqdm(filtered_authors):
        for coauthor in author2coauthor[authorID]:
            if coauthor['coauthor_id'] in filtered_authors_set:
                valid_authors.append(authorID)
                break

    log_text = 'From year {} to {}, there are {} authors with degree greater and equal to {}'.format(start_time, end_time, len(valid_authors), min_degree)
    log_list.append(log_text)
    print(log_text)
    return list(set(valid_authors)), author2coauthor

def create_graph(valid_authors, author2coauthor, output_dir):
    authorID2agentID = {}
    agentID2authorID = {}

    for agentID, authorID in enumerate(tqdm(valid_authors)):
        authorID2agentID[authorID] = agentID
        agentID2authorID[agentID] = authorID

    with open('{}/agentID2authorID.json'.format(output_dir), 'w') as json_file:
        json.dump(agentID2authorID, json_file, indent=4)

    adj_matrix = np.zeros((agent_num, agent_num), dtype=np.int32)
    weight_matrix = np.zeros((agent_num, agent_num), dtype=np.int32)

    for agentID, authorID in enumerate(tqdm(valid_authors)):
        for coauthor in author2coauthor[authorID]:
            try:
                # symmetry adj_matrix
                adj_matrix[agentID][authorID2agentID[coauthor['coauthor_id']]] = 1
                adj_matrix[authorID2agentID[coauthor['coauthor_id']]][agentID] = 1

                weight = max(weight_matrix[agentID][authorID2agentID[coauthor['coauthor_id']]],
                             max(weight_matrix[authorID2agentID[coauthor['coauthor_id']]][agentID], int(coauthor['weight'])))
                weight_matrix[agentID][authorID2agentID[coauthor['coauthor_id']]] = weight
                weight_matrix[authorID2agentID[coauthor['coauthor_id']]][agentID] = weight
            except:
                pass

    np.savetxt('{}/adj_matrix.txt'.format(output_dir), adj_matrix, fmt='%d', delimiter=' ')
    np.savetxt('{}/weight_matrix.txt'.format(output_dir), weight_matrix, fmt='%d', delimiter=' ')

def create_adjacency_matrix(output_dir):
    matrix = np.loadtxt('{}/adj_matrix.txt'.format(output_dir), dtype=int)
    row_sum = np.sum(matrix, axis = -1)
    mean_degree = np.mean(row_sum)
    degree_log = 'Mean degree of one-hop adjacency matrix is {}'.format(int(mean_degree))
    print(degree_log)
    log_list.append(degree_log)

    degree_int2word = ['one', 'two', 'three', 'four', 'five']
    A = matrix
    adjacency_matries = [A]
    for degree in range(2, 6):
        adjacency_matries.append(np.clip(np.matmul(adjacency_matries[-1], A), a_min=None, a_max=1))
        matrix = np.zeros(A.shape, dtype=int)
        for adjacency_matrix in adjacency_matries:
            matrix += adjacency_matrix
        matrix = np.clip(matrix, a_min=None, a_max=1)
        row_sum = np.sum(matrix, axis = -1)
        mean_degree = np.mean(row_sum)
        np.savetxt('{}/{}-hop_adj_matrix.txt'.format(output_dir, degree_int2word[degree-1]), matrix, fmt='%d', delimiter=' ')
        degree_log = 'Mean degree of {}-hop adjacency matrix is {}'.format(degree_int2word[degree-1], int(mean_degree))
        print(degree_log)
        log_list.append(degree_log)

if __name__=='__main__':
    # Example usage
    start_time = 2000
    end_time = 2010
    author_min_degree = 50
    author_min_paper = 50

    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    output_dir = f'{root_dir}/authors_degree_ge{author_min_degree}_from_year{start_time}to{end_time}'
    if os.path.exists(output_dir) == False:
        os.mkdir(output_dir)

    # potential authors
    authors = extract_authors(root_dir, start_time = start_time, end_time = end_time)

    # valid authors
    valid_authors, author2coauthor = extract_valid_authors(authors, author_min_degree, author_min_paper)
    agent_num = len(valid_authors)

    # create graph on agents
    create_graph(valid_authors, author2coauthor, output_dir)
    create_adjacency_matrix(output_dir)

    # write out data info
    with open('{}/README.txt'.format(output_dir), 'w') as file:
        for log in log_list:
            file.write(log + '\n')