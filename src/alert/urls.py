from django.urls import path

from . import views


app_name = "alert"

urlpatterns = [
    path("create-alert/", views.AlertView.as_view(), name="create-alert"),
    path("delete-alert/<int:alert_id>/", views.delete_alert, name="delete-alert"),
]
