# import hashid_field
import uuid
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from pgvector.django import L2Distance, VectorField
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

# from . import signals
from .querysets import PaperQuerySet, PaperTopicQuerySet


class AbstractBaseModel(models.Model):
    """
    An abstract model with fields/properties that should belong to all our models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "ah yes"


class PaperTopic(MPTTModel):
    name = models.CharField(max_length=255)
    abbrv = models.CharField(max_length=50, unique=True, null=True)
    parent = TreeForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PaperTopicQuerySet.as_manager()

    class MPTTMeta:
        order_insertion_by = ["name"]
        verbose_name_plural = _("Paper topics")

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("newsletter:topic_detail", args=(self.abbrv,))


class Paper(models.Model):
    topics = models.ManyToManyField(PaperTopic, related_name="papers")
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=300)
    paper_number = models.CharField(max_length=15, unique=True)
    subjects = models.CharField(max_length=300, null=True)
    main_page = models.URLField(unique=True)
    is_visible = models.BooleanField(default=True)
    abstract = models.TextField()
    summary = models.TextField(null=True)
    similar_papers = models.ManyToManyField("self")

    # Access paper
    pdf_url = models.URLField(unique=True)
    tex_source = models.URLField(unique=True, null=True)

    # References and Citations
    google_scholar = models.URLField(unique=True, null=True)
    semantic_scholar = models.URLField(unique=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PaperQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse("newsletter:paper_detail", args=(self.paper_number,))
    @classmethod
    def get_query_embedding(cls, query):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query)
        return query_embedding

    def generate_embeddings(self):
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
            (c, tokenizer.tokenize(c), self.get_query_embedding(c))
            for c in get_chunks(self.title + "\n" + self.abstract)
        )

        # 3. Save the embeddings information for each chunk
        paper_chunks = []
        for chunk_content, chunk_tokens, chunk_embedding in chunk_embeddings:
            paper_chunks.append(
                PaperChunks(
                    paper=self,
                    chunk=chunk_content,
                    token_count=len(chunk_tokens),
                    embedding=chunk_embedding,
                )
            )

        PaperChunks.objects.bulk_create(paper_chunks)

    @classmethod
    def search(cls, query=None):
        query = query or "Creating effective LLM/AI agents"
        # > expected result: list of Job Descriptions in descending order of relevance
        query_embedding = cls.get_query_embedding(query)

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
    
    def get_similar_papers(self):
        query_embedding = self.get_query_embedding(self.title)

        paper_chunks = PaperChunks.objects.annotate(
            distance=L2Distance("embedding", query_embedding)
        ).order_by("distance")[:3]

        unique_papers = []
        for chunk in paper_chunks:
            if chunk.paper.id not in unique_papers:
                unique_papers.append(chunk.paper)
        
        self.similar_papers.add(unique_papers)
        self.save()

    def save(self):
        if not self.tex_source:
            self.tex_source = self.main_page.replace("pdf", "src")
        if not self.google_scholar:
            self.google_scholar = f"https://scholar.google.com/scholar_lookup?arxiv_id={self.paper_number}"
        if not self.semantic_scholar:
            self.semantic_scholar = (
                f"https://api.semanticscholar.org/arXiv:{self.paper_number}"
            )
        return super().save()


class PaperChunks(AbstractBaseModel):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="chunks")
    chunk = models.TextField()
    token_count = models.IntegerField(null=True)
    embedding = VectorField(dimensions=384)

    def __str__(self):
        return f"{self.paper.title} - {self.chunk[:50]}"


class PaperSearchResult:
    def __init__(self, score, paper, chunks):
        self.score = score
        self.paper = paper
        self.chunks = chunks

    def __str__(self):
        return f"{self.score}: {self.paper.title}"


from alert.models import Alert


class Newsletter(AbstractBaseModel):
    topic = models.ForeignKey(
        PaperTopic, related_name="newsletters", on_delete=models.CASCADE, null=True
    )
    alert = models.ForeignKey(
        Alert, related_name="newsletters", on_delete=models.CASCADE, null=True
    )
    subject = models.CharField(max_length=255)
    content = RichTextField()
    schedule = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return str(self.topic)

    def save(self, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.subject)
        return super().save(**kwargs)
