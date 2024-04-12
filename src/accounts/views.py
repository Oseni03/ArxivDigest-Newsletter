from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, View, TemplateView
from django.contrib import messages

from .models import User
from .forms import EmailAuthForm, UserCreationForm


# Create your views here.
class EmailAuthView(View):
    def post(self, request, **kwargs):
        form = EmailAuthForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            user, created = User.objects.get_or_create(email=email)
            
            user.send_verification_email(created)
        
            context = {
                "user": user,
                "created": created,
            }
            return render(request, "accounts/thank-you.html", context)
        messages.error(request, f"Invalid email address!")
        return redirect("newsletter:home")


class ResendConfirmation(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email_address")
        user = get_object_or_404(User, email=email)
        user.send_verification_email(created=False)
        context = {
            "user": user,
            "created": False,
        }
        return render(request, "accounts/thank-you.html", context)


class EmailConfirmView(View):
    template_name = "accounts/subscription_confirm.html"

    def get(self, request, token, *args, **kwargs):
        user = get_object_or_404(User, token=token)
        subscribed = user.subscribe()

        login(request, user)
        return render(request, self.template_name, {"subscribed": subscribed})


class LoginView(TemplateView):
    template_name = "accounts/login.html"


class UnsubscribeView(View):
    template_name = "accounts/unsubscribe.html"

    def get(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        context = {
            "user": user,
            "unsubscribe": True,
        }
        return render(request, self.template_name, context)

    def post(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        user.unsubscribe()
        return render(request, "accounts/unsubscribe_successful.html")


class RegisterView(View):
    template_name = "accounts/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        form = UserCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("newsletter:newsletters")
        return render(request, self.template_name, {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("newsletter:home")
