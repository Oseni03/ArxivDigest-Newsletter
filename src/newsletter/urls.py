from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("topics/<str:slug>/", views.TopicDetailView.as_view(), name="topic_detail"),
    path(
        "abs/<str:paper_number>/",
        views.PaperDetailView.as_view(),
        name="paper_detail",
    ),
    path("newsletters/", views.NewsletterListView.as_view(), name="newsletters"),
    path(
        "topic-subscription/<topic_abbrv>/",
        views.topic_subscription,
        name="topic-subscription",
    ),
]
