from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .utils import send_welcome_email

User = get_user_model()


@receiver(post_save, sender=User)
def user_verification(sender, instance, created, **kwargs):
    if settings.NEWSLETTER_SEND_VERIFICATION:
        instance.send_verification_email(created, instance.request.tenant.schema_name)
    else:
        instance.verified = True
        instance.subscribed = True
        instance.save()

        signals.subscribed.send(
            sender=instance.__class__, instance=instance
        )
        send_welcome_email(instance.email)