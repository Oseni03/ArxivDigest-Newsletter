from django.urls import path
from django.contrib.auth.views import LoginView

from .views import (
    TopicDetailView,
    LatestTopicView,
    NewsletterListView,
    NewsletterSubscribeView,
    NewsletterUnsubscribeView,
    NewsletterSubscribeResendView,
    NewsletterSubscriptionConfirmView,
)
from .forms import AuthenticationForm


app_name = 'newsletter'

urlpatterns = [
    path('', LatestTopicView.as_view(), name='home'),
    path(
        'topics/<str:abbrv>/',
        TopicDetailView.as_view(),
        name='topic_detail'
    ),
    path('newsletters/', NewsletterListView.as_view(), name='newsletters'),
    path(
        'login/',
        LoginView.as_view(
            template_name="newsletter/login.html",
            extra_context={"source": "login"}),
        name='login'),
    path(
        'subscribe/',
        NewsletterSubscribeView.as_view(),
        name='newsletter_subscribe'),
    path(
        'subscribe/resend/',
        NewsletterSubscribeResendView.as_view(),
        name='newsletter_subscribe_resend'),
    path(
        'subscribe/confirm/<uuid:token>/',
        NewsletterSubscriptionConfirmView.as_view(),
        name='newsletter_subscription_confirm'
    ),
    path(
        'unsubscribe/',
        NewsletterUnsubscribeView.as_view(),
        name='newsletter_unsubscribe'
    ),
]
