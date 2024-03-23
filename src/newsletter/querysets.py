from django.db import models
from django.utils import timezone


class PaperTopicQuerySet(models.QuerySet):

    use_for_related_fields = True
    
    def parents(self):
        return self.filter(level=0)


class PaperQuerySet(models.QuerySet):

    use_for_related_fields = True

    def visible(self):
        return self.filter(is_visible=True)
