from django.urls import path, reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", FormView.as_view(
        template_name="accounts/register.html", 
        form_class=UserCreationForm, 
        success_url=reverse_lazy("accounts:login"), # change success-url to price page
    ), name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", views.logout, name="logout"),
    path("reset-password/", auth_views.PasswordResetView.as_view(
        template_name="accounts/reset_password.html",
        email_template_name="accounts/emails/email_template_name.html",
        subject_template_name="accounts/emails/subject_template_name.txt",
        html_email_template_name="accounts/emails/html_email_template_name.html",
        success_url=reverse_lazy("accounts:password_reset_done"),
    ), name="reset_password"),
    path("reset-password-done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
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
]