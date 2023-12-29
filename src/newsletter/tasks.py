from celery import shared_task
from langchain.document_loaders import DataFrameLoader

from .models import PaperTopic, Paper
from newsletter.vectorstore.pgvector_service import PgvectorService

from django.conf import settings

import os
import random
import tqdm
from bs4 import BeautifulSoup as bs
import urllib.request
import json
import datetime


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (X11; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.44',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.44'
]


def get_papers(field_abbr):
    NEW_SUB_URL = f'https://arxiv.org/list/{field_abbr}/new'  # https://arxiv.org/list/cs/new
    page = urllib.request.urlopen(NEW_SUB_URL, headers={'User-Agent': random.choice(user_agents)})
    soup = bs(page)
    content = soup.body.find("div", {'id': 'content'})

    # find the first h3 element in content
    h3 = content.find("h3").text   # e.g: New submissions for Wed, 10 May 23
    date = h3.replace("New submissions for", "").strip()
    
    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    assert len(dt_list) == len(dd_list)
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        paper_number = dt_list[i].text.strip().split(" ")[2].split(":")[-1]
        paper['main_page'] = arxiv_base + paper_number
        paper['paper_number'] = paper_number
        paper['date'] = date
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title: ", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text \
                            .replace("Authors:\n", "").replace("\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
        paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()
        new_paper_list.append(paper)
    return new_paper_list


def embed_papers(papers: list, columns: list=None):
    if not columns:
        columns = [
            'title', 'subjects',
            'paper_number', 'authors', 'main_page', 
            'pdf', 'date', 'abstract'
        ]
    df = pd.DataFrame(papers, columns)
    loader = DataFrameLoader(df, page_content_column="abstract")
    docs = loader.load()
    
    pg_vectorstore = PgvectorService(settings.CONNECTION_STRING)
    pg_vectorstore.update_collection(docs, collection_name=datetime.date.today().strftime("%d-%m-%Y"))


@shared_task
def get_new_papers():
    topics = PaperTopic.objects.parents()
    new_paper_count = 0
    new_paper_list = []
    for topic in topics:
        if topic.abbrv:
            papers = get_papers(topic.abbrv)
            for paper in papers:
                date_format = "%a, %d %b %y"
                formatted_date = datetime.datetime.strptime(paper["date"], date_format)
                subjects = paper["subjects"].split(";")
                topics_abbrev = [
                    sub.replace(")", "").split("(")[-1]
                    for sub in subjects
                ]
                subjs = []
                for abbrv in topics_abbrev:
                    sub = PaperTopic.objects.filter(abbrv=abbrv)
                    if sub.exists():
                        subjs.append(sub.first())
                subjs.append(topic)
                
                paper_obj, created = Paper.objects.get_or_create(
                    paper_number=paper["paper_number"],
                    pdf_url=paper["pdf"],
                    published_at    =formatted_date.date(),
                    defaults={
                        "abstract": paper["abstract"],
                        "main_page": paper["main_page"],
                        "title": paper["title"],
                        "authors": paper["authors"],
                    }
                )
                if created:
                    new_paper_count += 1
                    new_paper_list.append(paper)
                    paper_obj.topics.add(subjs)
                    paper_obj.save()
    embed_papers(new)
    return f"Saved paper count: {new_paper_count}"