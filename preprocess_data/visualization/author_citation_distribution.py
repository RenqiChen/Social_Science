import json
from tqdm import tqdm
import os
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

def extract_citations(root_dir, used_data_dir):
    # load database
    database_dir = os.path.join(root_dir, 'database.db')
    conn = sqlite3.connect(database_dir)
    cursor = conn.cursor()

    # load authors
    with open('{}/agentID2authorID.json'.format(os.path.join(root_dir, used_data_dir)), 'r') as file:
        agentID2authorID = json.load(file)

    # load affiliatioons
    citations = []
    for agentID, authorID in tqdm(agentID2authorID.items()):
        cursor.execute(f'SELECT citation_num FROM users WHERE id = {authorID}')
        rows = cursor.fetchall()
        citations.append(rows[0][0])
    return citations

def draw_citation_histogram(citations):
    # Create a DataFrame
    df = pd.DataFrame(citations, columns=['Citations'])

    # Plot the histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df['Citations'], bins=range(min(citations), max(citations), 200), edgecolor='black')

    plt.xticks(range(0, 16000, 1000),
               labels=range(0, 160, 10))

    # Show the plot
    # Add titles and labels
    plt.title('Histogram of Authors by Citation Range')
    plt.xlabel('Citation Range (x100)')
    plt.ylabel('Number of Authors')

    save_dir = 'results'
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    plt.savefig(f'{save_dir}/citation.png', bbox_inches='tight')

if __name__ == '__main__':
    # load the karate club graph
    root_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    used_data_dir = '156authors_degree_ge50_from_year2000to2010'
    citations = extract_citations(root_dir, used_data_dir)
    draw_citation_histogram(citations)