from .models import Category


def newsletter(request):
    return {
        "topics": Category.objects.all(),
    }
