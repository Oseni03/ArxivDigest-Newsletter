import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.conf import settings

from .utils import send_subscription_verification_email

from newsletter.models import PaperTopic
from subscription.models import Price


class CustomUserManager(BaseUserManager):
    """Custome user manager."""
    def create_user(self, email, password=None, **extra_kwargs):
        """Create and saves a User with the given email and password."""
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email),)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_kwargs):
        """Create and saves a superuser with the given email and password."""

        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model representing user in the system."""
    email = models.EmailField(
        verbose_name="Email",
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Subscriber 
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    verified = models.BooleanField(default=False)
    verification_sent_date = models.DateTimeField(blank=True, null=True)
    
    # newsletters
    subscribed_topics = models.ManyToManyField(PaperTopic, related_name="users", through="Subscription")
    
    # subscription
    is_paid_subscriber = models.BooleanField(default=False)
    plan = models.ForeignKey(Price, on_delete=models.SET_NULL, null=True)
    customer_id = models.CharField(max_length=300, null=True, blank=True)
    
    objects = CustomUserManager()
    USERNAME_FIELD = "email"

    def __str__(self):
        """Return string representation of the object."""
        return str(self.email)

    def has_perm(self, perm, obj=None):
        """Check if the user have a specific permission."""
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        """Check if the user have permissions to view the app `app_label."""
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        """Check if the user a member of staff."""
        # Simplest possible answer: All admins are staff
        return self.is_admin
    
    @property
    def subscribed(self):
        return self.filter(verified=True, is_active=True)
    
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
    
    def unsubscribe(self):
        from . import signals
        
        if self.is_active:
            self.is_active = False
            self.verified = False
            self.save()

            signals.unsubscribed.send(
                sender=self.__class__, instance=self
            )

            return True
    
    def send_verification_email(self, created):
        from . import signals
        
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
        )
        signals.email_verification_sent.send(
            sender=self.__class__, instance=self
        )

    def get_verification_url(self):
        return reverse(
            'newsletter:newsletter_subscription_confirm',
            kwargs={'token': self.token}
        )
    
    def subscribed_to(self, topic: PaperTopic):
        return topic in self.subscribed_topics.all()


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(PaperTopic, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)