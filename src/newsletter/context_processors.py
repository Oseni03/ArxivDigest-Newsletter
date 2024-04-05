from .models import PaperTopic
from .forms import SubscriberEmailForm

def newsletter(request):
    return {
        "topics": PaperTopic.objects.prefetch_related("children").parents(),
        "subscription_form": SubscriberEmailForm(),
    }