import json
import re
from tqdm import tqdm

def extract_coauthors(output_dir, filename):
    with open(filename, 'r') as file:
        data = file.read()

    # Split the data into blocks based on the author index
    coauthors_blocks = data.split('#')[1:]  # Ignore the first empty split

    author2coauthor = {}
    for block in tqdm(coauthors_blocks):
        info_str = block.strip('\n').split('\t')

        author1 = info_str[0]
        author2 = info_str[1]
        weight = info_str[2]
        if author1 not in author2coauthor.keys():
            author2coauthor[author1] = []
        if author2 not in author2coauthor.keys():
            author2coauthor[author2] = []

        author2coauthor[author1].append({
            'coauthor_id':author2,
            'weight':weight
        })

        author2coauthor[author2].append({
            'coauthor_id':author1,
            'weight':weight
        })

    with open('{}/author2coauthor.json'.format(output_dir), 'w') as json_file:
        json.dump(author2coauthor, json_file, indent=4)

if __name__=='__main__':
    # Example usage
    output_dir = '/home/bingxing2/ailab/group/ai4agr/shy/s4s'
    filename = 'AMiner-Coauthor.txt'
    extract_coauthors(output_dir, filename)
