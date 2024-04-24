from typing import Any
from django.db.models.query import QuerySet
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from .forms import SubscriberEmailForm
from .models import PaperTopic, Paper, Newsletter
from .utils.email_validator import email_is_valid

from accounts.models import User
from alert.forms import AlertForm
from alert.models import Alert


class HomeView(View):
    template_name = "newsletter/home.html"

    def get(self, request, *args, **kwargs):
        context = {}
        papers = Paper.objects.visible()
        paginator = Paginator(papers, 25)

        page_number = request.GET.get("page", None)
        page_obj = paginator.get_page(page_number)
        context["papers"] = page_obj
        return render(request, self.template_name, context)


class TopicDetailView(DetailView):
    model = PaperTopic
    template_name = "newsletter/topic_detail.html"
    slug_url_kwarg = "abbrv"
    slug_field = "abbrv"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        papers = Paper.objects.filter(topics=self.object).visible()
        paginator = Paginator(papers, 25)

        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["papers"] = page_obj
        return context


def parent_topic_detail(request, id):
    topic = PaperTopic.objects.get(id=id)
    return render(
        request, "newsletter/partials/_topic_list_modal.html", {"topic": topic}
    )


class PaperDetailView(DetailView):
    model = Paper
    template_name = "newsletter/paper_detail.html"
    slug_url_kwarg = "paper_number"
    slug_field = "paper_number"
    context_object_name = "paper"


class NewsletterListView(ListView):
    model = Newsletter
    template_name = "newsletter/newsletters.html"
    context_object_name = "newsletters"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["alert_form"] = AlertForm
        if self.request.user.is_authenticated:
            context["alerts"] = Alert.objects.filter(user=self.request.user)
        return context


@login_required
def topic_subscription(request, topic_abbrv: str):
    topic = get_object_or_404(PaperTopic, abbrv=topic_abbrv)
    user = request.user
    if topic in user.subscribed_topics.all():
        user.subscribed_topics.remove(topic)
    else:
        user.subscribed_topics.add(topic)
    user.save()

    current_url = request.htmx.current_url
    if "newsletters" in current_url:
        context = {
            "topics": PaperTopic.objects.prefetch_related("children").parents(),
        }
        return render(request, "newsletter/partials/_newsletter_list.html", context)
    else:
        return render(
            request, "newsletter/partials/_topic_header.html", {"topic": topic}
        )
