import json
import re
from tqdm import tqdm
import os
import numpy as np
import sqlite3
start_time = 2000
end_time = 2010
root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
# load database
global_database_name = 'global_database.db'
global_conn = sqlite3.connect(os.path.join(root_dir, global_database_name))
global_cursor = global_conn.cursor()
# load all papers
global_cursor.execute(f"SELECT * FROM papers WHERE year >= {start_time} AND year <= {end_time}")
paper_list = global_cursor.fetchall()
i=0
for _ in tqdm(range(len(paper_list))):
    # save txt
    paper = paper_list[_]
    id = paper[0]
    title = paper[1]
    authors = paper[2],
    affiliations = paper[3],
    year = paper[4],
    publication_venue = paper[5],
    paper_references = paper[6],
    abstract = paper[7]
    citation = paper[8]
    # 打开文件并写入元素内容
    paper_content = {}
    if abstract != None and citation!=None:
        if citation>10:
            # print(abstract)
            filename = f"./papers/paper_{i}.txt"
            paper_content['id'] = id
            paper_content['title'] = title
            paper_content['authors'] = authors
            paper_content['affiliations'] = affiliations
            paper_content['year'] = year
            paper_content['publication_venue'] = publication_venue
            paper_content['paper_references'] = paper_references
            paper_content['abstract'] = abstract
            paper_content['citation'] = citation
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(str(paper_content))
                i = i + 1
#             i = i + 1
print(i)
# close
global_cursor.close()
global_conn.close()