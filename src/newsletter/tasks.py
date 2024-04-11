from celery import shared_task
from langchain.schema import Document

from django.conf import settings
from newsletter.utils.pgvector_service import PgvectorService

import datetime


@shared_task(name="newsletter.embed_papers")
def embed_papers(papers: list):
    docs = [
        Document(
            paper.title + "\n" + paper.abstract,
            metadata={
                "id": paper.id,
                "paper_number": paper.paper_number,
            },
        )
        for paper in papers
    ]

    pg_vectorstore = PgvectorService(settings.CONNECTION_STRING)
    pg_vectorstore.update_collection(
        docs, collection_name=datetime.date.today().strftime("%d-%m-%Y")
    )
