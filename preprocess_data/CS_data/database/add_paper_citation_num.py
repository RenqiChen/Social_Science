import sqlite3
import os
import json
import re
from tqdm import tqdm
def add_paper_citation_num(root_dir):
    global_database_name = 'global_database.db'
    # connect to database, if it doesn't exist then build one
    conn = sqlite3.connect(os.path.join(root_dir, global_database_name))
    # create cursor
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM papers")
    all_papers = cursor.fetchall()

    paper_citation = {}
    for paper in tqdm(all_papers):
        refs = paper[6].split(';') if paper[6] is not None else None
        if refs is None:
            continue

        for ref in refs:
            ref = ref.strip()
            if ref not in paper_citation.keys():
                paper_citation[ref] = 1
            else:
                paper_citation[ref] += 1

    cursor.execute('ALTER TABLE papers ADD COLUMN citation_num INTEGER')
    for k, v in tqdm(paper_citation.items()):
        cursor.execute(f'UPDATE papers SET citation_num = {v} WHERE id = {int(k)}')

    conn.commit()
    cursor.close()
    conn.close()

if __name__=='__main__':
    # data dir
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    add_paper_citation_num(root_dir)