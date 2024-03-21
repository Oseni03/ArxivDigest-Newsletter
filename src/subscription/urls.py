from django.urls import path 

from . import views


app_name = "subscription"

urlpatterns = [
    path("pricing/", views.SubscriptionView.as_view(), name="pricing"),
    path('stripe-config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session),  # new
    path('billing-portal/', views.billing_portal),  # new
]