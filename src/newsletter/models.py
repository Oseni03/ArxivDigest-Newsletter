# import hashid_field
from typing import Iterable
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

# from . import signals
from .querysets import PaperQuerySet, PaperTopicQuerySet


class PaperTopic(MPTTModel):
    name = models.CharField(max_length=255)
    abbrv = models.CharField(max_length=50, unique=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = PaperTopicQuerySet.as_manager()
    
    class MPTTMeta:
        order_insertion_by = ['name']
        verbose_name_plural = 'Paper topics'
    
    def __str__(self):
        return str(self.name)
    
    def get_absolute_url(self):
        return reverse("newsletter:topic_detail", args=(self.abbrv,))


class Paper(models.Model):
    topics = models.ManyToManyField(PaperTopic, related_name='papers')
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=300)
    paper_number = models.CharField(max_length=15, unique=True)
    subjects = models.CharField(max_length=300, null=True)
    main_page = models.URLField(unique=True)
    is_visible = models.BooleanField(default=True)
    abstract = models.TextField()
    summary = models.TextField(null=True)

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
        ordering = ['-created_at']
        
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
            self.semantic_scholar = f"https://api.semanticscholar.org/arXiv:{self.paper_number}"
        return super().save()


class Newsletter(models.Model):
    topic = models.ForeignKey(PaperTopic, related_name="newsletter", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = RichTextField()
    schedule = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField()
    
    def __str__(self):
        return str(self.topic)
    
    def save(self, force_insert: bool = ..., force_update: bool = ..., using: str | None = ..., update_fields: Iterable[str] | None = ...) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(force_insert, force_update, using, update_fields)
    
