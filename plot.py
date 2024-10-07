import requests
import sys
sys.path.append('agentscope-main/src')
from agentscope.service import arxiv_search

def arxiv(query : str):
    """Given a query, retrieve k abstracts of similar papers from google scholar"""

    proxy = {
        'http':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
        'https':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
    }

    temp_results = arxiv_search(query, max_results = 1, proxy = proxy).content
    if isinstance(temp_results, dict):
        retrieval_results = temp_results['entries']
    else:
        retrieval_results = []
        print(temp_results)

    for paper in retrieval_results:
        paper_info = {
            'title': paper.get('title'),
            'authors': ','.join(paper.get('authors')),
            'abstract': paper.get('summary'),
            'pdf_url': paper.get('url'),
            'venue': paper.get('comment')
        }
        print(paper_info)
        break

def arxiv2semantic(arxiv_id):
    # 构造请求的 URL，使用 arXiv ID 作为参数
    url = f"https://api.semanticscholar.org/v1/paper/arXiv:{arxiv_id}"
    # 发起请求
    response = requests.get(url)
    # 检查请求是否成功
    if response.status_code == 200:
        # 解析响应的 JSON 数据
        data = response.json()

        # 获取并打印 Semantic Scholar 的 ID
        semantic_scholar_id = data.get("paperId")
        print(f"Semantic Scholar ID: {semantic_scholar_id}")
    else:
        semantic_scholar_id = None
        print(f"请求失败，状态码：{response.status_code}")
    return semantic_scholar_id

def semantic2info(semantic_scholar_id):
    # 构造请求的URL
    url = f"https://api.semanticscholar.org/v1/paper/{semantic_scholar_id}"

    # 发起请求
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print(f"请求失败，状态码：{response.status_code}")

if __name__ == '__main__':
    title = 'Quantum Computing for Climate Resilience and Sustainability Challenges'
    arxiv(title)
    arxiv_id = "2403.00825"
    semantic2info(arxiv2semantic(arxiv_id))