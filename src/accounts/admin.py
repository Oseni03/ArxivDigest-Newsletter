from django.contrib import admin

from .models import User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "subscribed",
        "verified",
        "token_expired",
        "verification_sent_date",
    )
    list_filter = (
        "verified",
        "verification_sent_date",
    )
    search_fields = ("email",)
    readonly_fields = ("created_at",)
    exclude = ("token",)


admin.site.register(User, UserAdmin)
