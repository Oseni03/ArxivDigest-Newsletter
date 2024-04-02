from newsletter.utils.arxiv import get_papers
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Loads the arxiv.org papers into the database'
    
    def handle(self, *args, **options):
        get_papers()
        self.stdout.write(self.style.SUCCESS('Load arxiv papers successfully'))