from django.urls import path 

from . import views


app_name = "subscription"

urlpatterns = [
    path("pricing/", views.PricingPage.as_view(), name="pricing"),
    path('stripe-config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session, name="checkout"),  # new
    path('billing-portal/', views.billing_portal, name="billing-portal"),  # new
]