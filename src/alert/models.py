from django.db import models
from django.utils.translation import gettext_lazy as _

from newsletter.models import Paper
from accounts.models import User, Schedule


# Create yourbn models here.
class Alert(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    schedule = models.CharField(
        max_length=15, choices=Schedule.choices, default=Schedule.WEEKLY
    )
    papers = models.ManyToManyField(Paper, related_name="alerts")
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
