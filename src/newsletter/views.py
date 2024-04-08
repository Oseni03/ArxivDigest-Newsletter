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


class HomeView(View):
    template_name = "newsletter/home.html"
    
    def get(self, request, *args, **kwargs):
        context = {}
        papers = Paper.objects.visible()
        paginator = Paginator(papers, 25)

        page_number = request.GET.get("page", None)
        page_obj = paginator.get_page(page_number)
        context["papers"] = page_obj
        if request.htmx:
            return render(request, "newsletter/partials/_paper_list.html", context)
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

    def get_template_names(self, *args, **kwargs):
        if self.request.htmx:
            return "newsletter/partials/_paper_list.html"
        return super().get_template_names()


class PaperDetailView(DetailView):
    model = Paper
    template_name = "newsletter/paper_detail.html"
    slug_url_kwarg = "paper_number"
    slug_field = "paper_number"
    context_object_name = "paper"


class NewsletterListView(LoginRequiredMixin, ListView):
    model = Newsletter
    template_name = "newsletter/newsletters.html"
    context_object_name = "newsletters"

    def post(self, request, **kwargs):
        data = dict(request.POST)
        categories = data.get("categories", [])
        if categories:
            topics = [
                get_object_or_404(PaperTopic, abbrv=category)
                for category in categories
            ]
            for topic in topics:
                request.user.subscribed_topics.add(topic)
            request.user.save()
        return render(request, self.template_name, {})


@login_required
def topic_subscription(request, topic_abbrv):
    topic = get_object_or_404(PaperTopic, abbrv=topic_abbrv)
    user = request.user
    if topic in user.subscribed_topics.all():
        user.subscribed_topics.remove(topic)
        user.save()
    else:
        user.subscribed_topics.add(topic)
        user.save()

    context = {
        "topics": PaperTopic.objects.prefetch_related("children").parents(),
    }
    return render(request, "newsletter/partials/_newsletter_list.html", context)


class NewsletterSubscribeView(View):
    template_name = "newsletter/newsletter_subscribe.html"

    def get(self, request, *args, **kwargs):
        context = {
            "source": "subscribe",
            "form": SubscriberEmailForm(),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = SubscriberEmailForm(request.POST)
        if form.is_valid():
            email_address = form.cleaned_data.get("email")

            user = User.objects.filter(email=email_address)

            if user.exists():
                return redirect("accounts:login")
            else:
                return render(
                    request,
                    "accounts/register.html",
                    {"form": UserCreationForm(initial={"username": email_address})},
                )
        else:
            context = {
                "source": "subscribe",
                "form": form,
            }
            for error in form.errors.values():
                messages.error(self.request, error)
            return render(request, self.template_name, context)


class ThankyouView(TemplateView):
    template_name = "newsletter/thank-you.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["send_verification"] = settings.NEWSLETTER_SEND_VERIFICATION
        return context
