import json
from newsletter.utils.arxiv import load_fields
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Loads the arxiv.org fields/topics into the database'
    
    def handle(self, *args, **options):
        with open("arxiv.json") as file:
            data = json.load(file)
        
        load_fields(data)
        self.stdout.write(self.style.SUCCESS('Load arxiv topics successfully'))
