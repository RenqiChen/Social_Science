import requests
from semanticscholar import SemanticScholar
from typing import List, Dict, Union
def search_for_papers(query, result_limit=5) -> Union[None, List[Dict]]:
    if not query:
        return None
    rsp = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": result_limit,
            "fields": "title,authors,venue,year,abstract,citationStyles,citationCount",
        },
    )
    print(f"Response Status Code: {rsp.status_code}")
    print(
        f"Response Content: {rsp.text[:500]}"
    )  # Print the first 500 characters of the response content
    rsp.raise_for_status()
    results = rsp.json()
    total = results["total"]
    time.sleep(1.0)
    if not total:
        return None

    papers = results["data"]
    return papers

def paper_search(query : str,
                 top_k : int = 5,
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
        retrieval_results = dblp_search_publications(query, num_results = 5)['content']
    else:
        temp_results = arxiv_search(query, max_results = 5, proxy = proxy).content
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
    # headers={"X-API-KEY": S2_API_KEY},
    # papers = search_for_papers('multi-modal learning')
    # print(papers[0])

    # sch = SemanticScholar()
    # results = sch.search_paper('multi-modal learning', limit = 5)
    # for item in results.items:
    #     print(item.title)

    res = paper_search('multi-modal learning')
    for r in res:
        print(r)