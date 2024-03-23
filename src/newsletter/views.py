from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.forms import UserCreationForm

from .forms import SubscriberEmailForm
from .models import PaperTopic, Paper, Newsletter
from .utils.email_validator import email_is_valid

from accounts.models import User


class TopicDetailView(SingleObjectMixin, ListView):
    paginate_by = 15
    template_name = "newsletter/topic_detail.html"
    slug_url_kwarg = 'abbrv'
    slug_field = 'abbrv'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(
            queryset=PaperTopic.objects.prefetch_related("subtopics", "papers__topics").all()
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = self.object
        return context

    def get_queryset(self):
        return self.object.papers.visible()


class PaperDetailView(View):
    template_name = "newsletter/paper_detail.html"

    def get(self, request, paper_number, *args, **kwargs):
        paper = get_object_or_404(Paper, paper_number=paper_number)
        return render(request, self.template_name, {"paper": paper})


class HomeView(TemplateView):
    template_name = "newsletter/home.html"

    def get_context_data(self, **kwargs):
        prefetch_papers = Paper.objects.visible().prefetch_related('topics')
        latest_topics = PaperTopic.objects.prefetch_related(
            Prefetch('papers', queryset=prefetch_papers)
        ).parents()

        context = super().get_context_data(**kwargs)
        context['topics'] = latest_topics
        context['subscription_form'] = SubscriberEmailForm()
        return context


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
            email_address = form.cleaned_data.get('email')
            
            user = User.objects.filter(email=email_address)
            
            if user.exists():
                return redirect("accounts:login")
            else:
                return render(request, "accounts/register.html", {"form": UserCreationForm(initial={"username": email_address})})
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


class NewsletterUnsubscribeView(TemplateView):
    template_name = "newsletter/newsletter_unsubscribe.html"
    
    def get_context_data(self):
        context = super().get_context_data()
        context["form"] = SubscriberEmailForm()
        return context

    def post(self, request, *args, **kwargs):
        form = SubscriberEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            subscriber = Subscriber.objects.filter(
                subscribed=True,
                email_address=email
            )
    
            if subscriber.exists():
                subscriber.first().unsubscribe()
                return render(request, "newsletter/newsletter_unsubscribed.html")
            else:
                messages.info(request, 'Subscriber with this e-mail address does not exist.')
                return redirect(reverse("newsletter:home"))
        context = {
            "form": form,
        }
        return render(request, self.template_name, context)
