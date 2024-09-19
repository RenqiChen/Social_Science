import sqlite3
import os
import json
import re
from tqdm import tqdm

def extract_paper_info(paper, year_range, least_citation, least_author = 3):
    # year info
    year = paper['year'] if isinstance(paper['year'], int) else None
    if year is None or year < year_range[0] or year > year_range[1]:
        return None

    # citation info
    n_citation = paper['n_citation'] if isinstance(paper['n_citation'], int) else None
    if n_citation is None or n_citation < least_citation:
        return None

    # author info
    authors = []
    for author in paper['authors']:
        if author['id'].strip()!='':
            authors.append(author['id'].strip())
    if len(authors) < least_author:
        return None

    # id info
    paper_id = paper['id'].strip()
    if paper_id=='':
        return None

    # title info
    title = paper['title'].strip()
    if title=='':
        return None

    # abstract info
    abstract = paper['abstract'].strip()
    if abstract=='':
        return None

    # keywords info
    keywords = paper['keywords']
    if len(keywords)==0:
        return None

    # reference info
    references = paper['references']
    if len(keywords)==0:
        return None

    # venue
    venue = paper['venue_id']
    if venue=='':
        return None

    return (paper_id, title, abstract,
            ';'.join(keywords), year, ';'.join(authors),
            ';'.join(references), n_citation, venue)

def create_paper_table(conn, cursor, root_dir, data_dir, year_range, n_citation):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='papers';")
    exists = cursor.fetchone() is not None
    if exists:
        print("Paper table already exists!")
    else:
        # create table
        print('build paper table...')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                keywords TEXT,
                year INTEGER,
                authors TEXT,
                paper_references TEXT,
                citation INTEGER,
                venue_id TEXT
            )
        ''')

        valid_authors = []
        for i in tqdm(range(1, 15)):
            count = 0
            # 逐行读取大文件
            with open(f'{root_dir}/v3.1_oag_publication_{i}.json', 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # 解析每一行的 JSON 对象
                        paper = json.loads(line.strip())
                        # 处理数据（例如，打印第一个字典）
                        paper_data = extract_paper_info(paper, year_range, n_citation)
                        if paper_data is not None:
                            # extract author info
                            valid_authors.extend(paper_data[5].split(';'))
                            valid_authors = list(set(valid_authors))
                            # Insert query
                            query = '''
                            INSERT INTO papers (id, title, abstract, keywords, year, authors, paper_references, citation, venue_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            '''

                            # Execute the query with user data
                            cursor.execute(query, paper_data)
                            count += 1
                        else:
                            pass
                    except:
                        pass

            print(f'{count} papers are valid')

        print(f"{len(valid_authors)} valid authors")
        agentID2authorID = {}
        for id, author in enumerate(valid_authors):
            agentID2authorID[str(id)] = author

        with open(f'{data_dir}/agentID2authorID.json', 'w') as json_file:
            json.dump(agentID2authorID, json_file, indent=4)

        conn.commit()

def create_author_table(conn, cursor, root_dir, data_dir):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='authors';")
    exists = cursor.fetchone() is not None
    if exists:
        print("authors table already exists!")
    else:
        # create table
        print('build author table...')
        cursor.execute('''
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

        # load author data
        with open(author_data_dir, 'r') as file:
            data = file.read()

        # Split the data into blocks based on the author index
        author_blocks = data.split('#index')[1:]  # Ignore the first empty split

        for block in tqdm(author_blocks):
            info_str = block.split('\n')

            author_id = info_str[0].strip()

            author_name = re.search(r'#n (.+)', info_str[1])
            if author_name is not None:
                author_name = author_name.group(1).strip().lower()

            author_affiliations = re.search(r'#a (.+)', info_str[2])
            if author_affiliations is not None:
                author_affiliations = author_affiliations.group(1).strip().lower()

            paper_count = re.search(r'#pc (.+)', info_str[3])
            if paper_count is not None:
                paper_count = paper_count.group(1).strip()

            citation_number = re.search(r'#cn (.+)', info_str[4])
            if citation_number is not None:
                citation_number = citation_number.group(1).strip()

            h_index = re.search(r'#hi (.+)', info_str[5])
            if h_index is not None:
                h_index = h_index.group(1).strip()

            p_index = re.search(r'#pi (.+)', info_str[6])
            if p_index is not None:
                p_index = p_index.group(1).strip()

            up_index = re.search(r'#upi (.+)', info_str[7])
            if up_index is not None:
                up_index = up_index.group(1).strip()

            research_topics = re.search(r'#t (.+)', info_str[8])
            if research_topics is not None:
                research_topics = research_topics.group(1).strip()

            # Define your user data (id, name, affiliation)
            author_data = (int(author_id),
                           author_name,
                           author_affiliations,
                           int(paper_count) if paper_count is not None else None,
                           int(citation_number) if citation_number is not None else None,
                           float(h_index) if h_index is not None else None,
                           float(p_index) if p_index is not None else None,
                           float(up_index) if up_index is not None else None,
                           research_topics)

            # Insert query
            query = '''
            INSERT INTO authors (id, name, affiliations, paper_num, citation_num, h_index, p_index, up_index, topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            # Execute the query with user data
            cursor.execute(query, author_data)

        conn.commit()

def create_publication_table(conn, cursor, publication_data_dir):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='publications';")
    exists = cursor.fetchone() is not None
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
        cursor.execute('''
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

        # load publication data
        with open(publication_data_dir, 'r') as file:
            publication_data = file.read()

        # Split the data into blocks based on the author index
        blocks = publication_data.split('\n')[:-1]  # Ignore the first empty split

        for block in tqdm(blocks):
            info_str = block.strip('\n').split('\t')
            authorID = int(info_str[1]) if info_str[1] is not None else None
            paperID = int(info_str[2]) if info_str[2] is not None else None
            if authorID is None or paperID is None:
                continue
            cursor.execute(f'SELECT year FROM papers WHERE id = {paperID}')
            year = cursor.fetchall()[0][0]

            # Define publication data
            publication_data = (authorID, paperID, year, 0)
            # Insert query
            query = '''
                INSERT INTO publications (author_id, paper_id, year, time_stamp)
                VALUES (?, ?, ?, ?)
                '''
            cursor.execute(query, publication_data)

        conn.commit()

def create_coauthor_table(conn, cursor, coauthor_data_dir):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='coauthors';")
    exists = cursor.fetchone() is not None
    if exists:
        print("Coauthors table already exists!")
        cursor.execute("SELECT * FROM coauthors")

        # 获取查询结果集:
        rows = cursor.fetchall()

        # 遍历结果集并打印每一行:
        for row in rows:
            print(row)
    else:
        # create table
        cursor.execute('''
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

        with open(coauthor_data_dir, 'r') as file:
            coauthor_data = file.read()

        # Split the data into blocks based on the author index
        coauthors_blocks = coauthor_data.split('#')[1:]  # Ignore the first empty split

        for block in tqdm(coauthors_blocks):
            info_str = block.strip('\n').split('\t')

            authorID = int(info_str[0]) if info_str[0] is not None else None
            coauthorID = int(info_str[1]) if info_str[1] is not None else None
            weight = float(info_str[2]) if info_str[2] is not None else None

            if authorID is None or coauthorID is None:
                continue

            # Define coauthor data
            coauthor_data = (authorID, coauthorID, 1, weight, 0)

            # Insert query
            query = '''
                    INSERT INTO coauthors (author_id, coauthor_id, hop_num, weight, time_stamp)
                    VALUES (?, ?, ?, ?, ?)
                    '''

            # Execute the query with user data
            cursor.execute(query, coauthor_data)

        conn.commit()

if __name__=='__main__':
    root_dir = '/home/bingxing2/ailab/group/ai4agr/crq/SciSci/OAG'
    year_range = [2000, 2010]
    least_n_citation = 150
    data_dir = f'/home/bingxing2/ailab/group/ai4agr/crq/SciSci/OAG/data_from_{year_range[0]}to{year_range[1]}_gt_{least_n_citation}_citation'
    if os.path.exists(data_dir) == False:
        os.mkdir(data_dir)

    # connect to database, if it doesn't exist then build one
    conn = sqlite3.connect(os.path.join(data_dir, 'database.db'))
    # create cursor
    cursor = conn.cursor()
    create_paper_table(conn, cursor, root_dir, data_dir, year_range, least_n_citation)

    # 关闭游标和连接
    cursor.close()
    conn.close()



    # valid_authors = []
    # for i in tqdm(range(1, 15)):
    #     count = 0
    #     # 逐行读取大文件
    #     with open(f'{root_dir}/v3.1_oag_publication_{i}.json', 'r', encoding='utf-8') as f:
    #         for line in f:
    #             try:
    #                 # 解析每一行的 JSON 对象
    #                 paper = json.loads(line.strip())
    #                 # 处理数据（例如，打印第一个字典）
    #                 paper_data = extract_paper_info(paper, year_range, least_n_citation)
    #                 if paper_data is not None:
    #                     count += 1
    #                 else:
    #                     pass
    #             except:
    #                 pass
    #     print(count)



    # # data dir

    # author_data_dir = 'AMiner-Author.txt'
    # paper_data_dir = 'AMiner-Paper.txt'
    # publication_data_dir = 'AMiner-Author2Paper.txt'
    # coauthor_data_dir = 'AMiner-Coauthor.txt'
    #
    # # connect to database, if it doesn't exist then build one
    # conn = sqlite3.connect(os.path.join(root_dir, global_database_name))
    # # create cursor
    # cursor = conn.cursor()
    #
    # # create user table
    # create_author_table(conn, cursor, os.path.join(root_dir, author_data_dir))
    # # create paper table
    # create_paper_table(conn, cursor, os.path.join(root_dir, paper_data_dir))
    # # create publication table
    # create_publication_table(conn, cursor, os.path.join(root_dir, publication_data_dir))
    # # create coauthor table
    # create_coauthor_table(conn, cursor, os.path.join(root_dir, coauthor_data_dir))
    #
    # # 关闭游标和连接
    # cursor.close()
    # conn.close()