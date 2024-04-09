from django.db import models

from newsletter.models import Paper
from accounts.models import User

# Create your models here.
class Alert(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    papers = models.ManyToManyField(Paper)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)