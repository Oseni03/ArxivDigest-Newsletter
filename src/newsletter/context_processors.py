from .models import Category


def newsletter(request):
    return {
        "categories": Category.objects.all(),
    }
