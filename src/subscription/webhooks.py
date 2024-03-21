import datetime
import logging

from django.utils import timezone
from djstripe import webhooks, models as djstripe_models

from .services import subscriptions, customers, charges

logger = logging.getLogger(__name__)


@webhooks.handler('invoice.payment_failed', 'invoice.payment_action_required')
def send_email_on_subscription_payment_failure(event: djstripe_models.Event):
    """
    This is an example of a handler that sends an email to a customer after a recurring payment fails

    :param event:
    :return:
    """
    notifications.SubscriptionErrorEmail(customer=event.customer).send()


@webhooks.handler('checkout.session.completed')
def checkout_completed(event: djstripe_models.Event):
    """Payment is successful and the subscription is created.
    You should provision the subscription and save the customer ID to your database.
    
    :param event:
    :return:
    """
    customer = event.customer
    pass


@webhooks.handler('invoice.paid')
def invoice_paid(event: djstripe_models.Event):
    """Continue to provision the subscription as payments continue to be made.
    Store the status in your database and check when a user accesses your service.
    This approach helps you avoid hitting rate limits.
    
    :param event:
    :return:
    """
    customer = event.customer
    pass


@webhooks.handler('invoice.payment_failed')
def invoice_payment_failed(event: djstripe_models.Event):
    """The payment failed or the customer does not have a valid payment method.
    The subscription becomes past_due. Notify your customer and send them to the
    customer portal to update their payment information.
    
    :param event:
    :return:
    """
    customer = event.customer
    pass
