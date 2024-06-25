from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("categories/<str:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("subscribe-modal/<str:slug>/", views.subscribe_modal, name="subscribe-modal"),
    path(
        "abs/<str:paper_number>/",
        views.PaperDetailView.as_view(),
        name="paper_detail",
    ),
    path(
        "topic-subscription/",
        views.topic_subscription,
        name="topic-subscription",
    ),
]
