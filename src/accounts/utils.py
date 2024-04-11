from django.conf import settings
from django.urls import reverse_lazy
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Email:

    def send(self, to_email, context, subject_temp, text_body_temp, html_body_temp):
        # Send context so that users can use context data in the subject
        subject = render_to_string(subject_temp, context).rstrip("\n")

        text_body = render_to_string(text_body_temp, context)
        html_body = render_to_string(html_body_temp, context)

        message = EmailMultiAlternatives(
            subject, text_body, settings.EMAIL_HOST_USER, [to_email]
        )

        message.attach_alternative(html_body, "text/html")
        message.send()


def send_subscription_verification_email(verification_url, to_email):
    """
    Sends verification e-mail to subscribers

    :param verification_url: subscribers unique verification url
    :param to_email: subscribers email
    """
    context = {"site_url": settings.DOMAIN_URL, "verification_url": verification_url}

    email = Email()
    email.send(
        to_email,
        context,
        "accounts/emails/email_verification_subject.txt",
        "accounts/emails/email_verification.txt",
        "accounts/emails/email_verification.html",
    )


def send_welcome_email(to_email):
    """
    Sends welcome e-mail to subscribers

    :param to_email: subscribers email
    """
    context = {
        "newsletters": reverse_lazy("newsletter:newsletters"),
        "site_url": settings.DOMAIN_URL,
    }

    email = Email()
    email.send(
        to_email,
        context,
        "accounts/emails/email_welcome_subject.txt",
        "accounts/emails/email_welcome.txt",
        "accounts/emails/email_welcome.html",
    )
