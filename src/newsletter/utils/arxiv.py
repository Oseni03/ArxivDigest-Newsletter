import json
import pprint
import requests
from bs4 import BeautifulSoup 
from urllib.parse import urljoin


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


def get_fields(url="https://www.arxiv.org"):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    fields = soup.select("main div#content h2")[:-1]
    
    fields_list = []
    for field in fields:
        subfields = field.next_sibling.next_sibling.select("li")
        subfields_list = []
        for f in subfields:
            sub = f.select_one("a")
            main_url = urljoin(url, sub.get("href"))
            subfields_list.append({
                "name": sub.text,
                "abbrv": f.select_one("strong").get("id"),
                "sub_fields": get_subsubfields(main_url)
            })

        fields_list.append({
            "name": field.text,
            "sub_fields": subfields_list,
        })
    
    return fields_list 



fields = get_fields()
with open("data/arxiv.json", "w") as file:
    json_data = json.dumps(fields, indent=4)
    file.write(json_data)