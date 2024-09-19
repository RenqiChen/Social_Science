from loguru import logger
import os
import sys
sys.path.append('agentscope-main/src')
from agentscope.memory import TemporaryMemory
from agentscope.service import (
    dblp_search_publications,  # or google_search,
    arxiv_search
)
def paper_search(query : str,
                 top_k : int = 8,
                 start_year : int = None,
                 end_year : int = None,
                 search_engine : str = 'arxiv') -> list:
    """Given a query, retrieve k abstracts of similar papers from google scholar"""

    proxy = {
        'http':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
        'https':'http://u-cEoRwn:EDvFuZTe@172.16.4.9:3128',
    }

    start_year = 0 if start_year is None else start_year
    end_year = 9999 if end_year is None else end_year
    papers = []
    if search_engine == 'google scholar':
        # retrieval_results = scholarly.search_pubs(query)
        retrieval_results = []
    elif search_engine == 'dblp':
        retrieval_results = dblp_search_publications(query, num_results = top_k)['content']
    else:
        temp_results = arxiv_search(query, max_results = top_k, proxy = proxy).content
        if isinstance(temp_results, dict):
            retrieval_results = temp_results['entries']
        else:
            retrieval_results = []
            print(temp_results)

    for paper in retrieval_results:

        if len(papers) >= top_k:
            break

        try:
            pub_year = paper.get('published', None)[:4]
        except:
            pub_year = paper.get('year', None)

        if pub_year and start_year <= int(pub_year) <= end_year:
            if search_engine == 'google scholar':
                paper_info = {
                    'title': paper.get('title'),
                    'authors': paper.get('authors'),
                    'year': pub_year,
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'venue': paper.get('venue')
                }
            elif search_engine == 'dblp':
                paper_info = {
                    'title': paper.get('title'),
                    'authors': paper.get('authors'),
                    'year': pub_year,
                    'abstract': paper.get('abstract'),
                    'url': paper.get('url'),
                    'venue': paper.get('venue')
                }
            else:
                paper_info = {
                    'title': paper.get('title'),
                    'authors': ','.join(paper.get('authors')),
                    'year': pub_year,
                    'abstract': paper.get('summary'),
                    'pdf_url': paper.get('url'),
                    'venue': paper.get('comment')
                }

            # print(paper_info)
            papers.append(paper_info)

    return papers

if __name__=='__main__':
    print(paper_search('multi-modal learning'))
