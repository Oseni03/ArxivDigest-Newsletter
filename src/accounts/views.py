from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, View

from .models import User

# Create your views here.
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
