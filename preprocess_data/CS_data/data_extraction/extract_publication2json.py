import json
import re
from tqdm import tqdm

def extract_papers_authors(output_dir, filename):
    with open(filename, 'r') as file:
        data = file.read()

    # Split the data into blocks based on the author index
    blocks = data.split('\n')[:-1]  # Ignore the first empty split

    paper2author = {}
    author2paper = {}
    for block in tqdm(blocks):
        info_str = block.strip('\n').split('\t')

        author = info_str[1]
        paper = info_str[2]

        if author not in author2paper.keys():
            author2paper[author] = []
        if paper not in paper2author.keys():
            paper2author[paper] = []

        author2paper[author].append(paper)
        paper2author[paper].append(author)

    with open('{}/author2paper.json'.format(output_dir), 'w') as json_file:
        json.dump(author2paper, json_file, indent=4)

    with open('{}/paper2author.json'.format(output_dir), 'w') as json_file:
        json.dump(paper2author, json_file, indent=4)

if __name__=='__main__':
    # Example usage
    output_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    filename = 'AMiner-Author2Paper.txt'
    extract_papers_authors(output_dir, filename)
