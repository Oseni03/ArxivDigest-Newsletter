from celery import shared_task

from .utils import send_welcome_email


@shared_task(name="accounts.welcome")
def send_welcome_email_task(to_email):
    send_welcome_email(to_email)
