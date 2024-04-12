from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views
from .decorators import login_not_required

app_name = "accounts"

urlpatterns = [
    path("subscribe/", views.EmailAuthView.as_view(), name="subscribe"),
    path(
        "subscribe/confirm/<uuid:token>/",
        views.EmailConfirmView.as_view(),
        name="email-confirmation",
    ),
    path(
        "resend-confirmation/",
        views.ResendConfirmation.as_view(),
        name="resend-confirmation",
    ),
    path(
        "login/",
        login_not_required(
            views.LoginView.as_view()
        ),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path(
        "unsubscribe/<int:user_id>/",
        views.UnsubscribeView.as_view(),
        name="unsubscribe",
    ),
]
