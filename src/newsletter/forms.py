from typing import Any
from django import forms
from django.utils.translation import gettext as _

from accounts.models import User
from newsletter.models import Category


class SubscriberEmailForm(forms.Form):
    email = forms.EmailField()


class SubscriptionForm(forms.ModelForm):
    email = forms.EmailField()
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all())

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("User with email already exist!")
        return email
