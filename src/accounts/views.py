from django.shortcuts import render
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def logout_view(request):
    logout(request)