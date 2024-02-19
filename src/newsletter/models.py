import uuid
# import hashid_field
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

# from . import signals
from .querysets import SubscriberQuerySet, PaperQuerySet, PaperTopicQuerySet
from .utils.send_verification import send_subscription_verification_email
from .utils.send_welcome import send_welcome_email


class PaperTopic(MPTTModel):
    name = models.CharField(max_length=255)
    abbrv = models.CharField(max_length=50, null=True)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = PaperTopicQuerySet.as_manager()
    
    class MPTTMeta:
        order_insertion_by = ['name']
        verbose_name_plural = 'Paper topics'
    
    def __str__(self):
        return str(self.name)
    
    def get_absolute_url(self):
        return reverse("newsletter:topic_detail", args=(self.abbrv,))


class Paper(models.Model):
    topics = models.ManyToManyField(PaperTopic, related_name='papers')
    title = models.CharField(max_length=255)
    paper_number = models.PositiveIntegerField()
    authors = models.CharField(max_length=255)
    main_page = models.URLField()
    pdf_url = models.URLField()
    is_visible = models.BooleanField(default=True)
    abstract = models.TextField()
    summary = models.TextField(null=True)
    published_at = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PaperQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return str(self.title)
    
    def get_absolute_url(self):
        return reverse("newsletter:paper_detail", args=(self.paper_number,))


class Newsletter(models.Model):
    topic = models.ForeignKey(PaperTopic, related_name="newsletter", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = RichTextField()
    schedule = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField()
    
    def __str__(self):
        return str(self.topic)


class Subscriber(models.Model):
    email_address = models.EmailField(unique=True)
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    verified = models.BooleanField(default=False)
    subscribed = models.BooleanField(default=False)
    snoozed = models.BooleanField(default=False)
    verification_sent_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = SubscriberQuerySet.as_manager()

    def __str__(self):
        return self.email_address

    def token_expired(self):
        if not self.verification_sent_date:
            return True

        expiration_date = (
            self.verification_sent_date + timezone.timedelta(
                days=settings.NEWSLETTER_EMAIL_CONFIRMATION_EXPIRE_DAYS
            )
        )
        return expiration_date <= timezone.now()

    def reset_token(self):
        unique_token = str(uuid.uuid4())

        while self.__class__.objects.filter(token=unique_token).exists():
            unique_token = str(uuid.uuid4())

        self.token = unique_token
        self.save()

    def subscribe(self):
        if not settings.NEWSLETTER_SEND_VERIFICATION or not self.token_expired():
            self.verified = True
            self.subscribed = True
            self.save()

            signals.subscribed.send(
                sender=self.__class__, instance=self
            )
            send_welcome_email(self.email_address)
            return True
    
    def unsubscribe(self):
        if self.subscribed:
            self.subscribed = False
            self.verified = False
            self.save()

            signals.unsubscribed.send(
                sender=Subscriber, instance=self
            )

            return True

    def snooze(self):
        if not self.snoozed:
            self.snoozed = True
            self.save()

            signals.snoozed.send(
                sender=self.__class__, instance=self
            )
            return True
    
    def unsnooze(self):
        if self.snoozed:
            self.snoozed = False
            self.save()

            signals.unsnoozed.send(
                sender=self.__class__, instance=self
            )
            return True
    
    def send_verification_email(self, created, niche):
        minutes_before = timezone.now() - timezone.timedelta(minutes=5)
        sent_date = self.verification_sent_date

        # Only send email again if the last sent date is five minutes earlier
        if sent_date and sent_date >= minutes_before:
            return

        if not created:
            self.reset_token()

        self.verification_sent_date = timezone.now()
        self.save()

        send_subscription_verification_email(
            self.get_verification_url(), 
            self.email_address,
            niche
        )
        signals.email_verification_sent.send(
            sender=self.__class__, instance=self
        )

    def get_verification_url(self):
        return reverse(
            'newsletter:newsletter_subscription_confirm',
            kwargs={'token': self.token}
        )


class Subscription(models.Model):
    subscriber = models.ForeignKey(Subscriber, related_name="subscriptions", on_delete=models.CASCADE)
    topic = models.ForeignKey(PaperTopic, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
