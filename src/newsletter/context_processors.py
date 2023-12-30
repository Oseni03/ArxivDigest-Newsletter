from .models import PaperTopic

def newsletter(request):
    return {
        "topics": PaperTopic.objects.parents()
    }