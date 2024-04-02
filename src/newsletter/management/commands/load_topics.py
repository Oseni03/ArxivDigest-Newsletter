import os
import json
from newsletter.utils.arxiv import get_fields, load_fields
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Loads the arxiv.org fields/topics into the database'
    
    def handle(self, *args, **options):
        if not os.path.exists("newsletter/utils/data/arxiv_topics.json"):
            get_fields()
        with open("newsletter/utils/data/arxiv_topics.json") as file:
            data = json.load(file)
        
        load_fields(data)
        self.stdout.write(self.style.SUCCESS('Load arxiv topics successfully'))
