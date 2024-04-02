import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def get_categories(url="https://arxiv.org"):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    topics = soup.select("div#content h2")
    for topic in topics:
        print(topic)
        print(topic.next_sibling)
    return


if __name__ == "__main__":
    categories = get_categories()
    print(categories)
    print(len(categories))