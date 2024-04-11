from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def login_not_required(function):
    def wrapper(request, *args, **kwargs):
        decorated_view_func = login_required(request)
        if decorated_view_func.user.is_authenticated:
            return redirect("newsletter:newsletters")
        else:
            return function(request, *args, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper
