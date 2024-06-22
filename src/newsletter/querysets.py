from django.db import models


class PaperQuerySet(models.QuerySet):

    use_for_related_fields = True

    def visible(self):
        return self.filter(is_visible=True)
