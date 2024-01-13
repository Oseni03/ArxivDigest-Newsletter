import django_filters

from .models import PaperTopic


def subtopics(request):
    if request is None:
        return PaperTopic.objects.none()
    
    # company = request.user.company
    return PaperTopic.objects.all()


class PaperSubTopicFilter(django_filters.FilterSet):
    children = filters.ModelChoiceFilter(queryset=subtopics)
    
    class Meta:
        model = PaperTopic
        fields = ["children"]