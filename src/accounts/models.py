from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


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
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

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