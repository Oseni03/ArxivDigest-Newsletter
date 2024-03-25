from django.urls import path 

from . import views


app_name = "subscription"

urlpatterns = [
    path("pricing/", views.PricingPage.as_view(), name="pricing"),
    path('create-checkout-session/', views.create_checkout_session, name="checkout"),  # new
    path('payment-success/', views.payment_successful, name="payment-success"), 
    path('billing-portal/', views.billing_portal, name="billing-portal"),  # new
    path('webhook/', views.webhook_received, name="webhook"),  # new
]