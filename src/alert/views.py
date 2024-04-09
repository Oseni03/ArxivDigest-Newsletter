from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Alert
from .forms import AlertForm

# Create your views here.
class AlertView(LoginRequiredMixin, View):

    def post(self, request, **kwargs):
        form = AlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
        alerts = Alert.objects.filter(user=request.user)
        return render(request, "alert/partials/_alert_list.html", {"alerts": alerts})


@csrf_exempt
def delete_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    if alert:
        alert.delete()
    alerts = Alert.objects.filter(user=request.user)
    return render(request, "alert/partials/_alert_list.html", {"alerts": alerts})