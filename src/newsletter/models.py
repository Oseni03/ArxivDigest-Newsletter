# import hashid_field
from django.db import models
from django.urls import reverse
from django.conf import settings

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

# from . import signals
from .querysets import PaperQuerySet, PaperTopicQuerySet


class PaperTopic(MPTTModel):
    name = models.CharField(max_length=255)
    abbrv = models.CharField(max_length=50, null=True)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subtopics')
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
    subjects = models.CharField(max_length=300, null=True)
    main_page = models.URLField(unique=True)
    pdf_url = models.URLField(unique=True)
    is_visible = models.BooleanField(default=True)
    abstract = models.TextField()
    summary = models.TextField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PaperQuerySet.as_manager()

    def __str__(self):
        return str(self.title)
    
    def get_absolute_url(self):
        return reverse("newsletter:paper_detail", args=(self.paper_number,))


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
    
