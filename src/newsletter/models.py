import uuid
# import hashid_field
from django.db import models
from django.urls import reverse
from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

from . import signals
from .app_settings import NEWSLETTER_EMAIL_CONFIRMATION_EXPIRE_DAYS
from .querysets import SubscriberQuerySet, PaperQuerySet, PaperTopicQuerySet
from .utils.send_verification import send_subscription_verification_email


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email).lower(),
        )
        user.set_password(password)
        group_user, _ = Group.objects.get_or_create(name="user")
        user.save(using=self._db)
        user.groups.add(group_user)
        UserProfile.objects.create(user=user)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email,
            password=password,
        )
        group_admin, _ = Group.objects.get_or_create(name="admin")
        user.is_active = True
        user.is_superuser = True
        user.groups.add(group_admin)
        user.save(using=self._db)
        return user

    def filter_admins(self):
        return self.filter(groups__name="admin")


class User(AbstractBaseUser, PermissionsMixin):
    # id = hashid_field.HashidAutoField(primary_key=True)
    created = models.DateTimeField(editable=False, auto_now_add=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self) -> str:
        return str(self.email)


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
    user = models.OneToOneField(User, related_name="subscriber", on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    verified = models.BooleanField(default=False)
    subscribed = models.BooleanField(default=False)
    verification_sent_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = SubscriberQuerySet.as_manager()

    def __str__(self):
        return str(self.email)
    
    @property
    def email(self):
        return self.user.email

    def token_expired(self):
        if not self.verification_sent_date:
            return True

        expiration_date = (
            self.verification_sent_date + timezone.timedelta(
                days=NEWSLETTER_EMAIL_CONFIRMATION_EXPIRE_DAYS
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
        if not self.token_expired():
            self.verified = True
            self.subscribed = True
            self.user.is_active = True
            self.user.save()
            self.save()

            signals.subscribed.send(
                sender=self.__class__, instance=self
            )

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

    def send_verification_email(self, created):
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
            self.get_verification_url(), self.email
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
    subscribers = models.ManyToManyField(Subscriber, related_name="subscriptions")
    topic = models.OneToOneField(PaperTopic, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @admin.display(description="Subscribers count")
    def subscribers_count(self):
        return f"{len(self.subscribers.all())}"