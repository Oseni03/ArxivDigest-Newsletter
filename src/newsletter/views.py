from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse
from django.contrib import messages
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.detail import SingleObjectMixin

from .forms import SubscriberEmailForm
from .models import PaperTopic, Paper, Subscriber, Newsletter
from .utils.email_validator import email_is_valid


class TopicDetailView(SingleObjectMixin, ListView):
    paginate_by = 15
    template_name = "newsletter/topic_detail.html"
    slug_url_kwarg = 'abbrv'
    slug_field = 'abbrv'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(
            queryset=PaperTopic.objects.prefetch_related("children", "papers__topics").all()
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


class NewsletterSubscribeView(FormView):
    form_class = SubscriberEmailForm
    template_name = "newsletter/newsletter_subscribe.html"
    success_url = settings.NEWSLETTER_SUBSCRIPTION_REDIRECT_URL

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["source"] = "subscribe"
        return context 
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        for error in form.errors.values():
            messages.error(self.request, error)
        return response
    
    def form_valid(self, form):
        email_address = form.cleaned_data.get('email')

        subscriber, created = Subscriber.objects.get_or_create(
            email_address=email_address
        )

        if not created and subscriber.subscribed:
            pass
            # messages.success(self.request, 'You have already subscribed to the newsletter.')
        else:
            if settings.NEWSLETTER_SEND_VERIFICATION:
                subscriber.send_verification_email(created, self.request.tenant.schema_name)
            else:
                if email_is_valid(subscriber.email_address):
                    subscriber.subscribe()
        return super().form_valid(form)


class ThankyouView(TemplateView):
    template_name = "newsletter/thank-you.html"
    
    def get_context_data(self):
        context = super().get_context_data()
        context["send_verification"] = settings.NEWSLETTER_SEND_VERIFICATION
        return context


class NewsletterSubscribeResendView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email_address")
        subscriber = get_object_or_404(Subscriber, email_address=email)
        subscriber.send_verification_email(created=False)
        return render(request, "newsletter/thank-you.html")


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


class NewsletterSubscriptionConfirmView(DetailView):
    template_name = "newsletter/newsletter_subscription_confirm.html"
    model = Subscriber
    slug_url_kwarg = 'token'
    slug_field = 'token'

    def get_queryset(self):
        return super().get_queryset().filter(verified=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        subscribed = self.object.subscribe()

        context = self.get_context_data(
            object=self.object, 
            subscribed=subscribed
        )
        return self.render_to_response(context)
