# import hashid_field
import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from pgvector.django import VectorField

from ckeditor.fields import RichTextField

from accounts.models import User

# from . import signals
from .querysets import PaperQuerySet


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


class Category(models.Model):
    name = models.CharField(max_length=255)
    abbrv = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(null=True, blank=True, unique=True)

    # newsletters
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="categories", through="Subscription")

    class MPTTMeta:
        order_insertion_by = ["name"]
        verbose_name_plural = _("categories")

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("newsletter:category-detail", args=(self.slug,))
    
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Paper(models.Model):
    categories = models.ManyToManyField(Category, related_name="papers")
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


class Newsletter(AbstractBaseModel):
    category = models.ForeignKey(
        Category, related_name="newsletters", on_delete=models.CASCADE, null=True
    )
    subject = models.CharField(max_length=255)
    content = RichTextField()
    schedule = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return str(self.category)

    def save(self, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.subject)
        return super().save(**kwargs)


class Subscription(AbstractBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"],
                name="unique_user_category",
            ),
        ]