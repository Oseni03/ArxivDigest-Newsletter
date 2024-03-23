from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from djstripe.settings import djstripe_settings
from djstripe import models as djstripe_models
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView
from django.views.decorators.http import require_POST

from .forms import SubscriptionForm
from .models import Product

# Create your views here.
class PricingPage(ListView):
    template_name = "subscription/pricing.html"
    model = Product 
    context_object_name = "products"
    

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@login_required
@require_POST
def create_checkout_session(request):
    price = request.POST.get("price")
    domain_url = settings.DOMAIN_URL
    stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
    (customer, _) = djstripe_models.Customer.get_or_create(request.user)
    try:
        session = stripe.checkout.Session.create(
            client_reference_id=customer.id,
            customer=customer.id,
            success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'cancel/',
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price': price,
                    'quantity': 1,
                }
            ],
        )
        return redirect(session.url)
    except Exception as e:
        # RETURN CUSTOM SERVER ERROR PAGE
        return JsonResponse({'error': str(e)})


@login_required
def billing_portal(request):
    domain_url = settings.DOMAIN_URL
    stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
    (customer, _) = djstripe_models.Customer.get_or_create(request.user)
    session = stripe.billing_portal.Session.create(
        customer=customer,
        return_url=f"{domain_url}/newsletters",
    )
    return redirect(session.url)