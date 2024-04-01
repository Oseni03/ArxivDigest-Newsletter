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
    path("thank-you/", views.ThankyouView.as_view(), name="thank-you"),
]
