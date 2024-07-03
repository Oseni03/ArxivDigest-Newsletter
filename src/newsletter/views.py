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

from .forms import SubscriberEmailForm, SubscriptionForm
from .models import Category, Paper, Newsletter
from .utils.email_validator import email_is_valid


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


class CategoryDetailView(DetailView):
    model = Category
    template_name = "newsletter/topic_detail.html"
    slug_url_kwarg = "slug"
    slug_field = "slug"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        papers = Paper.objects.filter(topics=self.object).visible()
        paginator = Paginator(papers, 25)

        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["papers"] = page_obj
        return context


class PaperDetailView(DetailView):
    model = Paper
    template_name = "newsletter/paper_detail.html"
    slug_url_kwarg = "paper_number"
    slug_field = "paper_number"
    context_object_name = "paper"


class NewsletterView(FormView):
    form_class = SubscriptionForm
    template_name = "newsletter/subscription.html"


@login_required
def topic_subscription(request, slug):
    topic = get_object_or_404(Category, slug=slug)
    user = request.user
    if topic in user.categories.all():
        user.categories.remove(topic)
    else:
        user.categories.add(topic)
    user.save()

    current_url = request.htmx.current_url
    if "newsletters" in current_url:
        context = {
            "topics": Category.objects.all(),
        }
        return render(request, "newsletter/partials/_newsletter_list.html", context)
    else:
        return render(
            request, "newsletter/partials/_topic_header.html", {"topic": topic}
        )


def subscribe_modal(request, slug):
    if slug == "all":
        pass
    else:
        category = get_object_or_404(Category, slug=slug)
        return render(
            request, "newsletter/partials/_subscribe_modal.html", {"category": category}
        )
