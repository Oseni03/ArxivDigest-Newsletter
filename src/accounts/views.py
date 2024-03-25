from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, View, FormView
from django.contrib import messages
from django.contrib.auth import login

from .models import User
from .forms import UserCreationForm

# Create your views here.
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


class ResendVerification(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email_address")
        user = get_object_or_404(User, email=email)
        user.send_verification_email(created=False)
        return redirect("newsletter:home")


class SubscriptionConfirmView(DetailView):
    template_name = "accounts/newsletter_subscription_confirm.html"
    model = User
    slug_url_kwarg = 'token'
    slug_field = 'token'

    def get_queryset(self):
        return super().get_queryset().filter(verified=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        subscribed = self.object.subscribe()

        context = self.get_context_data(
            object=self.object, 
            subscribed=subscribed
        )
        return self.render_to_response(context)
