from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace="accounts")),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path('subscription/', include('subscription.urls', namespace="subscription")),
    path('', include('newsletter.urls', namespace="newsletter")),
]
