from celery import shared_task
from langchain.schema import Document

from pgvector.django import L2Distance
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from django.conf import settings
from newsletter.models import Paper, PaperChunks
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


class PaperSearchResult:
    def __init__(self, score, paper, chunks):
        self.score = score
        self.paper = paper
        self.chunks = chunks

    def __str__(self):
        return f"{self.score}: {self.paper.title}"


def get_query_embedding(query):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(query)
    return query_embedding


def generate_embeddings(paper: Paper):
    def get_chunks(content, chunk_size=750):
        """Naive chunking of job description.

        `chunk_size` is the number of characters per chunk.
        """
        chunk_size = chunk_size
        while content:
            chunk, content = content[:chunk_size], content[chunk_size:]
            yield chunk

    # 1. Set up the tokenizer model
    tokenizer = AutoTokenizer.from_pretrained(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # 2. Chunk the paper description into sentences
    chunk_embeddings = (
        (c, tokenizer.tokenize(c), get_query_embedding(c))
        for c in get_chunks(paper.title + "\n" + paper.abstract)
    )

    # 3. Save the embeddings information for each chunk
    paper_chunks = []
    for chunk_content, chunk_tokens, chunk_embedding in chunk_embeddings:
        paper_chunks.append(
            PaperChunks(
                paper=paper,
                chunk=chunk_content,
                token_count=len(chunk_tokens),
                embedding=chunk_embedding,
            )
        )

    PaperChunks.objects.bulk_create(paper_chunks)


@classmethod
def search(query=None):
    query = query or "Creating effective LLM/AI agents"
    # > expected result: list of Job Descriptions in descending order of relevance
    query_embedding = get_query_embedding(query)

    paper_chunks = PaperChunks.objects.annotate(
        distance=L2Distance("embedding", query_embedding)
    ).order_by("distance")

    unique_papers = {}
    for chunk in paper_chunks:
        if chunk.paper.id not in unique_papers:
            unique_papers[chunk.paper.id] = {
                "paper": chunk.paper,
                "chunks": [chunk],
            }
        else:
            unique_papers[chunk.paper.id]["chunks"].append(chunk)

    results = []
    for k, v in unique_papers.items():
        score = sum([c.distance for c in v["chunks"]]) / len(v["chunks"])
        paper = v["paper"]
        results.append(PaperSearchResult(score, paper, v["chunks"]))

    return sorted(results, key=lambda r: r.score)


def get_similar_papers(paper: Paper):
    query_embedding = get_query_embedding(paper.title)

    paper_chunks = PaperChunks.objects.annotate(
        distance=L2Distance("embedding", query_embedding)
    ).order_by("distance")[:3]

    unique_papers = []
    for chunk in paper_chunks:
        if chunk.paper.id not in unique_papers:
            unique_papers.append(chunk.paper)
    
    paper.similar_papers.add(unique_papers)
    paper.save()
