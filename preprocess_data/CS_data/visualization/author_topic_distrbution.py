import json
from tqdm import tqdm
import os
import sqlite3

replace_dict = {
    'univ.':'university',
    'dept.':'department'
}

def affiliation_str_clean(affiliation):
    for k, v in replace_dict.items():
        affiliation = affiliation.replace(k, v)
    affiliation = affiliation.replace('  ', ' ')
    return affiliation

def extract_topics(root_dir, used_data_dir):
    # load database
    database_dir = os.path.join(root_dir, 'global_database.db')
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()

    # load authors
    with open('{}/agentID2authorID.json'.format(os.path.join(root_dir, used_data_dir)), 'r') as file:
        agentID2authorID = json.load(file)

    # load affiliatioons
    all_topics = {}
    for agentID, authorID in tqdm(agentID2authorID.items()):
        cursor.execute(f'SELECT topics FROM users WHERE id = {authorID}')
        rows = cursor.fetchall()
        topics = rows[0][0].split(';')
        for topic in topics:
            topic_splits = topic.strip().split(',')
            for topic_split in topic_splits:
                try:
                    all_topics[topic_split.strip()] += 1
                except:
                    all_topics[topic_split.strip()] = 1

    return all_topics

if __name__ == '__main__':
    # load the karate club graph
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    used_data_dir = '156authors_degree_ge50_from_year2000to2010'
    topics = extract_topics(root_dir, used_data_dir)
    topics = [[k, v] for k, v in topics.items()]
    topics = sorted(topics, key=lambda x:x[1], reverse=True)

    # save result
    save_dir = 'results'
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    with open(f'{save_dir}/topic.txt', 'w') as file:
        file.write(f"there are {len(topics)} topics\n")
        for topic in topics:
            file.write(f"{topic[0]}:{topic[1]}\n")