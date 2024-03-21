from django.urls import path

from . import views

app_name = 'newsletter'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path(
        'topics/<str:abbrv>/',
        views.TopicDetailView.as_view(),
        name='topic_detail'
    ),
    path(
        'topics/<int:paper_number>/',
        views.PaperDetailView.as_view(),
        name='paper_detail'
    ),
    path('newsletters/', views.NewsletterListView.as_view(), name='newsletters'),
    path(
        'subscribe/',
        views.NewsletterSubscribeView.as_view(),
        name='newsletter_subscribe'),
    path(
        'subscribe/resend/',
        views.NewsletterSubscribeResendView.as_view(),
        name='newsletter_subscribe_resend'),
    path("thank-you/", views.ThankyouView.as_view(), name="thank-you"),
    path(
        'subscribe/confirm/<uuid:token>/',
        views.NewsletterSubscriptionConfirmView.as_view(),
        name='newsletter_subscription_confirm'
    ),
    path(
        'unsubscribe/',
        views.NewsletterUnsubscribeView.as_view(),
        name='newsletter_unsubscribe'
    ),
]
