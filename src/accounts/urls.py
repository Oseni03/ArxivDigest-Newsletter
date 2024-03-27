from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views
from .decorators import login_not_required

app_name = "accounts"

urlpatterns = [
    path("register/", login_not_required(views.RegisterView.as_view()), name="register"),
    path("login/", login_not_required(auth_views.LoginView.as_view(template_name="accounts/login.html")), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/reset_password.html",
        email_template_name="accounts/emails/email_template_name.html",
        subject_template_name="accounts/emails/subject_template_name.txt",
        html_email_template_name="accounts/emails/html_email_template_name.html",
        success_url=reverse_lazy("accounts:password_reset_done"),
    ), name="reset_password"),
    path("password-reset-done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
    ), name="password_reset"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
    path(
        'resend-verification/',
        views.ResendVerification.as_view(),
        name='resend-verification'),
    path(
        'subscribe/confirm/<uuid:token>/',
        views.SubscriptionConfirmView.as_view(),
        name='subscription_confirm'
    ),
    path(
        'unsubscribe/<int:user_id>/',
        views.UnsubscribeView.as_view(),
        name='unsubscribe'
    ),
]