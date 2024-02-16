from .models import PaperTopic
from .forms import SubscriberEmailForm

def newsletter(request):
    return {
        "topics": PaperTopic.objects.parents(),
        "subscription_form": SubscriberEmailForm(),
    }