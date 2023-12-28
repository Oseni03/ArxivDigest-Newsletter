from django import forms
from django.utils.translation import gettext as _

from .models import User


class SubscriberEmailForm(forms.Form):
    email = forms.EmailField()


class AuthenticationForm(forms.ModelForm):
    password = forms.CharField(required=True, widget=forms.PasswordInput(), help_text=_("Enter password"))
    
    class Meta:
        model = User 
        fields = ("email", "password",)