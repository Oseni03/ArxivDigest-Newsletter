from celery import shared_task

from .utils import send_welcome_email


@shared_task(name='accounts.unsnooze')
def unsnooze(subscriber_id: int):
    from .models import User
    
    try:
        subscriber = User.objects.get(id=subscriber_id)
        subscriber.unsnooze()
    except:
        pass


@shared_task(name='accounts.welcome')
def send_welcome_email_task(to_email):
    send_welcome_email(to_email)