from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Product(models.Model):
    stripe_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class Price(models.Model):
    class IntervalChoice(models.TextChoices):
        MONTHLY = "MON", _("Mon")
        YEARLY = "YR", _("Yr")

    stripe_id = models.CharField(max_length=255, unique=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="prices"
    )
    name = models.CharField(max_length=150, null=True)
    currency = models.CharField(max_length=4)
    amount = models.IntegerField(default=0)
    interval = models.CharField(
        max_length=25, choices=IntervalChoice.choices, default=IntervalChoice.MONTHLY
    )
    features = models.TextField(null=True, help_text="Comma separated features.")
    is_free = models.BooleanField(default=False)
    has_trial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.amount)

    class Meta:
        ordering = ["amount"]


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    price = models.ForeignKey(Price, on_delete=models.PROTECT)
    stripe_checkout_session_id = models.CharField(max_length=500)
    payment_status = models.CharField(max_length=15)
    is_successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
