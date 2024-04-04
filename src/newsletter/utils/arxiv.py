import json
import os
import tqdm
import json
import pytz
import datetime
import requests
import threading
import urllib.request
from bs4 import BeautifulSoup 
from urllib.parse import urljoin
from django.db import transaction

from newsletter.models import PaperTopic, Paper


def get_subsubfields(url="https://arxiv.org/archive/astro-ph"):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    subsubfields_list = []
    try:
        fields = soup.select_one("main div#content h2").next_sibling.next_sibling.select("li")
        for field in fields:
            obj = field.select_one("b").get_text()
            name = obj.split(" - ")[-1]
            abbrv = obj.split(" - ")[0]
            subsubfields_list.append({
                "name": name,
                "abbrv": abbrv,
            })
    except:
        pass
    return subsubfields_list


def get_fields(url="https://www.arxiv.org", path="newsletter/utils/data/arxiv_topics.json"):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    fields = soup.select("main div#content h2")[:-1]
    
    fields_list = []
    for field in fields:
        subfields = field.next_sibling.next_sibling.select("li")
        subfields_list = []
        for f in subfields:
            sub = f.select_one("a")
            abbrv = f.select_one("strong").get("id")
            main_url = urljoin(url, f"/archive/{abbrv}")
            subfields_list.append({
                "name": sub.text,
                "abbrv": abbrv,
                "sub_fields": get_subsubfields(main_url)
            })

        fields_list.append({
            "name": field.text,
            "sub_fields": subfields_list,
        })
    
    with open(path, "w") as file:
        json_data = json.dumps(fields_list, indent=4)
        file.write(json_data)
    return fields_list


def load_fields(fields: list, parent_field: PaperTopic = None):
    for field in fields:
        if parent_field:
            topic = PaperTopic.objects.create(name=field["name"], abbrv=field.get("abbrv", None), parent=parent_field)
        else:
            topic = PaperTopic.objects.create(name=field["name"], abbrv=field.get("abbrv", None))
        
        sub_fields = field.get("sub_fields", [])
        if sub_fields:
            load_fields(sub_fields, topic)


def _download_new_papers(field_abbr, path):
    NEW_SUB_URL = (
        f"https://arxiv.org/list/{field_abbr}/new"  # https://arxiv.org/list/cs/new
    )
    page = urllib.request.urlopen(NEW_SUB_URL)
    soup = BeautifulSoup(page, "html.parser")
    content = soup.body.find("div", {"id": "content"})

    # find the first h3 element in content
    h3 = content.find("h3").text  # e.g: New submissions for Wed, 10 May 23
    date = h3.replace("New submissions for", "").strip()

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    assert len(dt_list) == len(dd_list)
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        paper_number = dt_list[i].text.strip().split(" ")[2].split(":")[-1]
        paper["main_page"] = arxiv_base + paper_number
        paper["pdf"] = arxiv_base.replace("abs", "pdf") + paper_number

        paper["title"] = (
            dd_list[i]
            .find("div", {"class": "list-title mathjax"})
            .text.replace("Title: ", "")
            .strip()
        )
        paper["authors"] = (
            dd_list[i]
            .find("div", {"class": "list-authors"})
            .text.replace("Authors:\n", "")
            .replace("\n", "")
            .strip()
        )
        paper["subjects"] = (
            dd_list[i]
            .find("div", {"class": "list-subjects"})
            .text.replace("Subjects: ", "")
            .strip()
        )
        paper["abstract"] = (
            dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()
        )
        new_paper_list.append(paper)
    
    #  check if ./data exist, if not, create it
    if not os.path.exists(path):
        os.makedirs(path)

    # save new_paper_list to a jsonl file, with each line as the element of a dictionary
    date = datetime.date.fromtimestamp(
        datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp()
    )
    date = date.strftime("%a, %d %b %y")
    with open(f"{path}/{field_abbr}_{date}.jsonl", "w") as file:
        json_data = json.dumps(new_paper_list, indent=4)
        file.write(json_data)
    return new_paper_list


def load_papers(result, topic_id):
    with transaction.atomic():
        for paper_data in result:
            # Create or get the Paper object within an atomic transaction
            paper, _ = Paper.objects.get_or_create(
                authors=paper_data["authors"],
                title=paper_data["title"],
                main_page=paper_data["main_page"],
                pdf_url=paper_data["pdf"],
                abstract=paper_data["abstract"]
            )
            # Assign the topic to the Paper object
            paper.topics.add(topic_id)
            paper.save()
        
    return result


def get_papers(limit=None, path="newsletter/utils/data/papers"):
    
    results = []

    if not os.path.exists(path):
        topics = PaperTopic.objects.all()
        threads = []

        for topic in topics:
            if topic.abbrv:
                date = datetime.date.fromtimestamp(
                    datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp()
                )
                date = date.strftime("%a, %d %b %y")
                if not os.path.exists(f"{path}/{topic.abbrv}_{date}.jsonl"):
                    result = _download_new_papers(topic.abbrv, path)
                else:
                    result = []
                    with open(f"{path}/{topic.abbrv}_{date}.jsonl", "r") as f:
                        for i, line in enumerate(f.readlines()):
                            if limit and i == limit:
                                return result
                            result.append(json.loads(line))
                
                thread = threading.Thread(target=load_papers, args=(result, topic.id))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

    return results



if __name__ == "__main__":
    # fields = get_fields()
    
    # load_fields(fields)
    
    papers = get_papers("cs.AI")
    print(papers)