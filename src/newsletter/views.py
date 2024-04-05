from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from .forms import SubscriberEmailForm
from .models import PaperTopic, Paper, Newsletter
from .utils.email_validator import email_is_valid

from accounts.models import User


class HomeView(ListView):
    model = Paper
    paginate_by = 25    
    template_name = "newsletter/home.html"
    context_object_name = "papers"
    
    def get_template_names(self, *args, **kwargs):
        if self.request.htmx:
            return "newsletter/partials/_paper_list.html"
        return super().get_template_names()


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


class PaperDetailView(View):
    template_name = "newsletter/paper_detail.html"

    def get(self, request, paper_number, *args, **kwargs):
        paper = get_object_or_404(Paper, paper_number=paper_number)
        return render(request, self.template_name, {"paper": paper})


class NewsletterListView(ListView):
    model = Newsletter
    template_name = "newsletter/newsletters.html"


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
