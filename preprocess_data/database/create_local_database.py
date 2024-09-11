import sqlite3
import os
import json
import re
from tqdm import tqdm

def create_paper_table(global_conn, local_conn, start_year, end_year):
    global_cursor = global_conn.cursor()
    local_cursor = local_conn.cursor()

    local_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='papers';")
    exists = local_cursor.fetchone() is not None
    if exists:
        print("Paper table already exists!")
    else:
        # create table
        print('build paper table...')
        local_cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY,
                title TEXT,
                authors TEXT,
                affiliations TEXT,
                year INTEGER,
                publication_venue TEXT,
                paper_references TEXT,
                abstract TEXT
            )
        ''')

        # extract papers in time range
        global_cursor.execute(f'SELECT id FROM papers WHERE year >= {start_year} AND year <= {end_year}')
        papers_in_range = global_cursor.fetchall()

        # create local paper table
        for paper in tqdm(papers_in_range):
            global_cursor.execute(f'SELECT * FROM papers WHERE id = {paper[0]}')
            # Insert query
            query = '''
            INSERT INTO papers (id, title, authors, affiliations, year, publication_venue, paper_references, abstract)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            # Execute the query with user data
            local_cursor.execute(query, global_cursor.fetchall()[0])

        global_cursor.close()
        local_cursor.close()
        local_conn.commit()

def create_author_table(global_conn, local_conn, root_dir):
    global_cursor = global_conn.cursor()
    local_cursor = local_conn.cursor()

    local_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='authors';")
    exists = local_cursor.fetchone() is not None
    if exists:
        print("Author table already exists!")
    else:
        # create table
        print('build author table...')
        local_cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                affiliations TEXT,
                paper_num INTEGER,
                citation_num INTEGER,
                h_index REAL,
                p_index REAL,
                up_index REAL,
                topics TEXT
            )
        ''')

        # paper2author
        with open('{}/paper2author.json'.format(root_dir), 'r') as file:
            paper2author = json.load(file)

        # extract authors in range
        print('extract authors in range...')
        local_cursor.execute(f'SELECT id FROM papers')
        papers_in_range = local_cursor.fetchall()

        authors = []
        valid_paper_num = 0
        for paper in tqdm(papers_in_range):
            try:
                authors.append(int(paper2author[str(paper[0])]))
                valid_paper_num += 1
            except:
                pass

        print("{} papers are valid".format(valid_paper_num))
        authors = set(authors)
        print("{} authors are included".format(len(authors)))

        print('insert authors to local database...')
        for author in tqdm(authors):
            global_cursor.execute(f'SELECT * FROM authors WHERE id = {author}')
            # Insert query
            query = '''
            INSERT INTO authors (id, name, affiliations, paper_num, citation_num, h_index, p_index, up_index, topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            # Execute the query with user data
            local_cursor.execute(query, global_cursor.fetchall()[0])

        global_cursor.close()
        local_cursor.close()
        local_conn.commit()

def create_publication_table(global_conn, local_conn):
    global_cursor = global_conn.cursor()
    local_cursor = local_conn.cursor()

    local_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='publications';")
    exists = local_cursor.fetchone() is not None
    if exists:
        print("Publication table already exists!")
        # cursor.execute("SELECT * FROM publications")
        #
        # # 获取查询结果集:
        # rows = cursor.fetchall()
        #
        # # 遍历结果集并打印每一行:
        # for row in rows:
        #     print(row)
    else:
        # create table
        print('create publication table...')
        local_cursor.execute('''
            CREATE TABLE IF NOT EXISTS publications (
                relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                paper_id INTEGER,
                year INTEGER,
                time_stamp INTEGER,
                FOREIGN KEY (author_id) REFERENCES users(id),
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            )
        ''')

        # extract publications in range
        print('extract publications in range...')
        local_cursor.execute(f'SELECT id FROM papers')
        papers_in_range = local_cursor.fetchall()
        for paper in tqdm(papers_in_range):
            global_cursor.execute(f'SELECT * FROM publications WHERE paper_id = {paper[0]}')
            publications = global_cursor.fetchall()
            for publication in publications:
                # Insert query
                query = '''
                INSERT INTO publications (relation_id, author_id, paper_id, year, time_stamp)
                VALUES (?, ?, ?, ?, ?)
                '''
                # Execute the query with user data
                local_cursor.execute(query, publication)

        global_cursor.close()
        local_cursor.close()
        local_conn.commit()

def create_coauthor_table(global_conn, local_conn):
    global_cursor = global_conn.cursor()
    local_cursor = local_conn.cursor()

    local_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='coauthors';")
    exists = local_cursor.fetchone() is not None
    if exists:
        print("Coauthors table already exists!")
        local_cursor.execute("SELECT * FROM coauthors")

        # 获取查询结果集:
        rows = cursor.fetchall()

        # 遍历结果集并打印每一行:
        for row in rows:
            print(row)
    else:
        # create table
        print("Create coauthor table...")
        local_cursor.execute('''
            CREATE TABLE IF NOT EXISTS coauthors (
                relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                coauthor_id INTEGER,
                hop_num INTEGER,
                weight REAL,
                time_stamp INTEGER,
                FOREIGN KEY (author_id) REFERENCES authors(id),
                FOREIGN KEY (coauthor_id) REFERENCES authors(id)
            )
        ''')

        # extract authors in range
        print('extract authors in range...')
        local_cursor.execute(f'SELECT id FROM authors')
        authors_in_range = local_cursor.fetchall()
        authors = []
        for author in authors_in_range:
            authors.append(author[0])
        authors = set(authors)

        # extract valid coauthors
        print('insert coauthors to local database...')
        global_cursor.execute(f'SELECT * FROM coauthors')
        coauthors_in_range = global_cursor.fetchall()
        for coauthor in tqdm(coauthors_in_range):
            if coauthor[1] in authors and coauthor[2] in authors:
                # Insert query
                query = '''
                INSERT INTO coauthors (relation_id, author_id, coauthor_id, hop_num, weight, time_stamp)
                VALUES (?, ?, ?, ?, ?, ?)
                '''
                # Execute the query with user data
                local_cursor.execute(query, coauthor)

        global_cursor.close()
        local_cursor.close()
        local_conn.commit()

if __name__=='__main__':
    # global data dir
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    global_database_name = 'global_database.db'
    global_conn = sqlite3.connect(os.path.join(root_dir, global_database_name))

    # local data dir
    start_year = 2000
    end_year = 2010
    local_dir_name = f'local_data_from_year{start_year}to{end_year}'
    local_dir = os.path.join(root_dir, local_dir_name)
    if os.path.exists(local_dir) == False:
        os.mkdir(local_dir)
    local_database_name = 'local_database.db'
    local_conn = sqlite3.connect(os.path.join(local_dir, local_database_name))

    # create paper table in time range
    create_paper_table(global_conn, local_conn, start_year, end_year)
    # # create user table
    create_author_table(global_conn, local_conn, root_dir)
    # # create publication table
    create_publication_table(global_conn, local_conn)
    # # create coauthor table
    create_coauthor_table(global_conn, local_conn)

    global_conn.close()
    local_conn.close()