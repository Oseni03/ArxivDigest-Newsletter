from django.contrib import admin

from .models import Product, Price


# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name",)


class PriceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "amount",
        "currency",
        "interval",
        "is_free",
        "has_trial",
        "active",
    )


admin.site.register(Product, ProductAdmin)
admin.site.register(Price, PriceAdmin)
