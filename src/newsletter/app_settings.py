from django.conf import settings
from django.urls import reverse_lazy


NEWSLETTER_EMAIL_BATCH_WAIT = getattr(
    settings, 'NEWSLETTER_EMAIL_BATCH_WAIT', 0
)
NEWSLETTER_EMAIL_BATCH_SIZE = getattr(
    settings, 'NEWSLETTER_EMAIL_BATCH_SIZE', 0
)
NEWSLETTER_EMAIL_CONFIRMATION_EXPIRE_DAYS = getattr(
    settings, 'NEWSLETTER_EMAIL_CONFIRMATION_EXPIRE_DAYS', 3
)
NEWSLETTER_SITE_BASE_URL = getattr(
    settings, 'NEWSLETTER_SITE_BASE_URL', 'http://127.0.0.1:8000'
)
NEWSLETTER_SUBSCRIPTION_REDIRECT_URL = getattr(
    settings, 'NEWSLETTER_SUBSCRIPTION_REDIRECT_URL',
    reverse_lazy('newsletter:home')
)
NEWSLETTER_UNSUBSCRIPTION_REDIRECT_URL = getattr(
    settings, 'NEWSLETTER_UNSUBSCRIPTION_REDIRECT_URL',
    reverse_lazy('newsletter:home')
)
