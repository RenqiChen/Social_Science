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

def extract_affiliations(root_dir, data_dir):
    # load database
    database_dir = os.path.join(root_dir, 'global_database.db')
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()

    # load authors
    with open('{}/agentID2authorID.json'.format(data_dir), 'r') as file:
        agentID2authorID = json.load(file)

    # load affiliatioons
    affiliations = {}
    for agentID, authorID in tqdm(agentID2authorID.items()):
        cursor.execute(f'SELECT affiliations FROM authors WHERE id = {authorID}')
        rows = cursor.fetchall()
        affis = rows[0][0].split(';')
        for affi in affis:
            affi_split = affi.strip().split(',')
            affi1 = affiliation_str_clean(affi_split[0].strip())
            try:
                affiliations[affi1] += 1
            except:
                affiliations[affi1] = 1
            if len(affi_split)>=3:
                affi2 = affiliation_str_clean(affi_split[1].strip())
                try:
                    affiliations[affi2] += 1
                except:
                    affiliations[affi2] = 1

    return affiliations

if __name__ == '__main__':
    # load the karate club graph
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    used_data_dir = 'authors_degree_ge50_from_year2000to2010'
    affiliations = extract_affiliations(root_dir, os.path.join(root_dir, used_data_dir))
    affiliations = [[k, v] for k, v in affiliations.items()]
    affiliations = sorted(affiliations, key=lambda x:x[1], reverse=True)

    # save result
    save_dir = 'results'
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    with open(f'{save_dir}/affiliation.txt', 'w') as file:
        file.write(f"there are {len(affiliations)} affiliations\n")
        for affi in affiliations:
            file.write(f"{affi[0]}:{affi[1]}\n")