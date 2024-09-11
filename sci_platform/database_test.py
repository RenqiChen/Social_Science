import json
import re
from tqdm import tqdm
import os
import numpy as np
import sqlite3

def save2database(paper_list : list[dict], output_dir : str):
    # connect to database, if it exists then delete it
    if os.path.isfile(output_dir):
        os.remove(output_dir)
    conn = sqlite3.connect(output_dir)
    # create cursor
    cursor = conn.cursor()

    # create table
    print('build paper table...')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY,
                title TEXT,
                authors TEXT,
                cite_papers TEXT,
                abstract TEXT
            )
        ''')

    for paper in paper_list:
        id = int(paper['id'])
        title = paper['title']
        abstract = paper['abstract']
        if paper['authors']!=None:
            authors = ';'.join(paper['authors'])
            paper_references = ';'.join(map(str, paper['cite_papers']))
        else:
            authors = None
            paper_references = None

        # Define your user data (id, name, affiliation)
        paper_data = (id,
                      title,
                      authors,
                      paper_references,
                      abstract)
        print(paper_data)

        # Insert query
        query = '''
            INSERT INTO papers (id, title, authors, cite_papers, abstract)
            VALUES (?, ?, ?, ?, ?)
            '''

        # Execute the query with user data
        cursor.execute(query, paper_data)

    conn.commit()
    cursor.close()
    conn.close()

file_dict={}
file_dict['title']='title'
file_dict['abstract']='abstract'
file_dict['id'] = 1
file_dict['authors'] = 'authors'
file_dict['cite_papers'] = 'papers'

paper_dicts = [file_dict]
output_dir = "/home/bingxing2/ailab/scxlab0066/SocialScience/database/database.db"
save2database(paper_dicts, output_dir)

root_dir = '/home/bingxing2/ailab/scxlab0066/SocialScience/database'
# load database
global_database_name = 'database.db'
global_conn = sqlite3.connect(os.path.join(root_dir, global_database_name))
global_cursor = global_conn.cursor()
# load all papers
paper_list = global_cursor.execute('SELECT * FROM papers').fetchall()
i=0
# save txt
print(len(paper_list))
paper = paper_list[(len(paper_list)-1)]
id = paper[0]
title = paper[1]
authors = paper[2]
affiliations = paper[3]
year = paper[4]
print(authors)
# close
global_cursor.close()
global_conn.close()