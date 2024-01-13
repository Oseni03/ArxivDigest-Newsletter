from django import forms
from django.utils.translation import gettext as _


class SubscriberEmailForm(forms.Form):
    email = forms.EmailField()
