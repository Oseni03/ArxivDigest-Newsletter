from django.db import models
from django.utils.translation import gettext_lazy as _

from newsletter.models import Paper
from accounts.models import User

# Create your models here.
class Alert(models.Model):
    class Schedule(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        BI_WEEKLY = "BI_WEEKLY", _("Bi Weekly")
        TRI_WEEKLY = "TRI_WEEKLY", _("Tri Weekly")

    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    schedule = models.CharField(max_length=15, choices=Schedule.choices, default=Schedule.WEEKLY)
    papers = models.ManyToManyField(Paper)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)