from django.shortcuts import redirect


def is_paid_subscriber(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_paid_subscriber:
            return redirect("subscription:pricing")
        else:
            return function(request, *args, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper