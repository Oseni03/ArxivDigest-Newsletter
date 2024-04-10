from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Paper
from .utils.chains import summarizer


@receiver(post_save, sender=Paper)
def paper_abstract_summarizer(sender, instance, created, **kwargs):
    if created:
        summary = summarizer(instance.abstract)
        instance.summary = summary
        instance.save()