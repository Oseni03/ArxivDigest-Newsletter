from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse 
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse
from django.contrib import messages
from django.views.generic import DetailView, FormView, ListView, TemplateView, View
from django.views.generic.detail import SingleObjectMixin

from .app_settings import (
    NEWSLETTER_SUBSCRIPTION_REDIRECT_URL,
    NEWSLETTER_UNSUBSCRIPTION_REDIRECT_URL,
)
from .forms import SubscriberEmailForm, AuthenticationForm
from .models import PaperTopic, Paper, Subscriber, Newsletter, User
from .utils.check_ajax import is_ajax


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


class LatestTopicView(TemplateView):
    template_name = "newsletter/home.html"

    def get_context_data(self, **kwargs):
        prefetch_papers = Paper.objects.visible().prefetch_related('topics')
        latest_topics = PaperTopic.objects.prefetch_related(
            Prefetch('papers', queryset=prefetch_papers)
        ).parents()

        context = super().get_context_data(**kwargs)
        context['topics'] = latest_topics
        return context


class NewsletterListView(ListView):
    model = Newsletter
    template_name = "newsletter/newsletters.html"


class SubscriptionAjaxResponseMixin(FormView):
    """Mixin to add Ajax support to the subscription form"""
    
    message = ''
    success = False

    def form_invalid(self, form):
        response = super().form_invalid(form)

        if is_ajax(self.request):
            return JsonResponse(
                form.errors.get_json_data(),
                status=400
            )
        else:
            messages.error(self.request, self.message)
            return response

    def form_valid(self, form):
        response = super().form_valid(form)

        if is_ajax(self.request):
            data = {
                'message': self.message,
                'success': self.success
            }
            return JsonResponse(data, status=200)
        else:
            messages.success(self.request, self.message)
            return response


class NewsletterSubscribeView(TemplateView):
    form_class = AuthenticationForm
    template_name = "newsletter/newsletter_subscribe.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["form"] = AuthenticationForm()
        context["source"] = "subscribe"
        return context 
    
    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            
            user = User.objects.filter(email=email)
            if user.exists():
                messages.info(request, 'You have already subscribed to the newsletter.')
                return redirect(reverse("newsletter:login"))
            else:
                user = form.save()
                user.set_password(form.cleaned_data.get("password"))
                user.save()
                subscriber = Subscriber.objects.get(user=user)
                subscriber.send_verification_email(created=False)
                return render(request, "newsletter/thank-you.html")
        else:
            for error in form.errors.values():
                messages.info(request, error)
        context = {
            "form": form,
        }
        return render(request, self.template_name, context)


class NewsletterSubscribeResendView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email_address")
        user = get_object_or_404(User, email=email)
        subscriber = Subscriber.objects.get(user=user)
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
                user__email=email
            ).first()
    
            if subscriber:
                subscriber.unsubscribe()
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
