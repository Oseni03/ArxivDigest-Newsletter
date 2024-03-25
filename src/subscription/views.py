import time
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from djstripe import models as djstripe_models
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import HttpResponse

from .forms import SubscriptionForm
from .models import Product, Payment, Price

from accounts.models import User

# Create your views here.
class PricingPage(ListView):
    template_name = "subscription/pricing.html"
    model = Product 
    context_object_name = "products"


@login_required
@require_POST
def create_checkout_session(request):
    price = request.POST.get("price")
    domain_url = f"{request.scheme}://{request.get_host()}/"
    stripe.api_key = settings.STRIPE_SECRET_KEY
    #(customer, _) = djstripe_models.Customer.get_or_create(request.user)
    try:
        session = stripe.checkout.Session.create(
            client_reference_id=request.user.id,
            customer_email=request.user.email,
            success_url=domain_url + 'subscription/payment-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + "subscription/pricing/",
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
        messages.info(request, str(e))
        return redirect("subscription:pricing")


@login_required
def payment_successful(request):
    user = request.user
    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session_id = request.GET.get("session_id", None)
    session = stripe.checkout.Session.retrieve(checkout_session_id)
    line_items = stripe.checkout.Session.list_line_items(checkout_session_id)["data"]
    customer = stripe.Customer.retrieve(session.customer)
    if not user.customer_id and user.email==customer["email"]:
        user.customer_id = customer["id"]
        user.save()
    price_id = line_items[0]["price"].get("id", None)
    price = Price.objects.get(stripe_id=price_id)
    
    payment = Payment.objects.create(
        user=user,
        price=price,
        stripe_checkout_session_id=checkout_session_id,
        payment_status=session.payment_status,
        created_at=session.created
    )
    messages.success(request, "Payment successful!")
    return redirect("newsletter:newsletters")


@login_required
def billing_portal(request):
    domain_url = f"{request.scheme}://{request.get_host()}"
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.billing_portal.Session.create(
        customer=request.user.customer_id,
        return_url=f"{domain_url}/newsletters",
    )
    return redirect(session.url)


@csrf_exempt
def webhook_received(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = '{{STRIPE_WEBHOOK_SECRET}}'
    request_data = json.loads(request.data)
    
    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        # signature = request.META["HTTP_STRIPE_SIGNATURE"]
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, 
                sig_header=signature, 
                secret=webhook_secret
            )
            data = event['data']
        except Exception as e:
            return HttpResponse(400)
            # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']
    
    if event_type == 'checkout.session.completed':
        # Payment is successful and the subscription is created.
        # You should provision the subscription and save the customer ID to your database.
        print(data)
        session = data["object"]
        session_id = session.get("id")
        time.sleep(15)
        payment = get_object_or_404(Payment, checkout_session_id=session_id)
        payment.is_successful = True 
        payment.save()
    elif event_type == 'invoice.paid':
        # Continue to provision the subscription as payments continue to be made.
        # Store the status in your database and check when a user accesses your service.
        # This approach helps you avoid hitting rate limits.
        print(data)
    elif event_type == 'invoice.payment_failed':
        # The payment failed or the customer does not have a valid payment method.
        # The subscription becomes past_due. Notify your customer and send them to the
        # customer portal to update their payment information.
        print(data)
    else:
        print('Unhandled event type {}'.format(event_type))
    return HttpResponse(200)