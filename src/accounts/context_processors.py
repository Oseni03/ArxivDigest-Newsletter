from .forms import EmailAuthForm


def accounts(request):
    return {
        "subscription_form": EmailAuthForm(),
    }
