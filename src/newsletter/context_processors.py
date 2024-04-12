from .models import PaperTopic


def newsletter(request):
    return {
        "topics": PaperTopic.objects.prefetch_related("children").parents(),
    }
