from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", views.logout, name="logout"),
    path("reset-password/", auth_views.PasswordResetView.as_view(
        template_name="reset_password.html",
        email_template_name="emails/email_template_name.html",
        subject_template_name="emails/subject_template_name.txt",
        html_email_template_name="emails/html_email_template_name.html",
        success_url=reverse_lazy("accounts:password_reset_done"),
    ), name="reset_password"),
    path("reset-password-done/", auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
    ), name="reset_password"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name="password_reset_complete"),
]