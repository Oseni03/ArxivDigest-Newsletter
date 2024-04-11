from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.dispatch import Signal
from django_celery_beat.models import PeriodicTask

from .utils import send_welcome_email

import stripe
import datetime


# Sent after email verification is sent, with Subscriber instance
email_verification_sent = Signal()

# Sent after subscription confirmed, with Subscriber instance
subscribed = Signal()

# Sent after unsubscription is successful, with Subscriber instance
unsubscribed = Signal()

# Sent after subscription is snoozed successful, with Subscriber instance
snoozed = Signal()


User = get_user_model()


@receiver(post_save, sender=User)
def create_stripe_customer(sender, instance, created, **kwargs):
    if created:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer = stripe.Customer.create(
            email=instance.email,
        )
        instance.customer_id = customer.get("id", None)
        instance.save()


@receiver(post_save, sender=User)
def user_verification(sender, instance, created, **kwargs):
    if created:
        if settings.NEWSLETTER_SEND_VERIFICATION:
            instance.send_verification_email(
                created, instance.request.tenant.schema_name
            )
        else:
            instance.verified = True
            instance.is_active = True
            instance.save()

            subscribed.send(sender=instance.__class__, instance=instance)
            send_welcome_email(instance.email)
