from datetime import datetime
import logging
import time
from typing import List

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from accounts.models import Schedule
from newsletter.models import Newsletter, Paper
from .models import Alert

User = get_user_model()


logger = logging.getLogger(__name__)


class NewsletterEmailSender:
    """The main class that handles sending email newsletters"""

    def __init__(self, alerts: List[Alert] = None, schedule: Schedule = None):
        self.alerts = self._get_alerts(alerts=alerts)
        # Schedule
        self.schedule = schedule
        # Size of each batch to be sent
        self.batch_size = settings.NEWSLETTER_EMAIL_BATCH_SIZE
        # list of alerts that were sent
        self.sent_alerts = []
        # list of newsletters that were sent
        self.sent_newsletters = []
        # Waiting time after each batch (in seconds)
        self.per_batch_wait = settings.NEWSLETTER_EMAIL_BATCH_WAIT
        # connection to the server
        self.connection = get_connection()
        self.email_host_user = settings.EMAIL_HOST_USER

    @staticmethod
    def _get_alerts(alerts=None):
        """
        gets alerts to be sent

        :param alerts: Alert QuerySet
        :param schedule: Schedule instance
            will not be sent
        """

        if alerts is None:
            alerts = Alert.objects.all()

        return alerts

    @staticmethod
    def _render_newsletter(alert: Alert, user):
        """renders newsletter template and returns Newsletter object"""
        subject = f"ArxivDigest - {alert.name}"
        papers = Paper.objects.filter(alerts=alert, is_visible=True)

        context = {
            "alert": alert,
            "papers": papers,
            "unsubscribe_url": reverse("accounts:unsubscribe", args=(user.id,)),
            "site_url": settings.DOMAIN_URL,
        }

        html = render_to_string("newsletter/email/newsletter_email.html", context)

        rendered_newsletter, created = Newsletter.objects.get_or_create(
            alert=alert,
            subject=subject,
            content=html,
            slug=slugify(subject)
        )

        return rendered_newsletter, created

    def _generate_email_message(self, to_email, rendered_newsletter):
        """
        Generates email message for an email_address

        :param to_email: user email address
        :param rendered_newsletter: rendered html of the newsletter with subject
        """
        message = EmailMessage(
            subject=rendered_newsletter.subject,
            body=rendered_newsletter.content,
            from_email=self.email_host_user,
            to=[to_email],
            connection=self.connection,
        )
        message.content_subtype = "html"

        return message

    def _get_batch_email_messages(self, alert: Alert):
        """
        Yields EmailMessage list in batches

        :param alert: Alert object/instance
        """
        subscriber_emails = User.objects.filter(
            alerts=alert, alerts__schedule=self.schedule
        )

        # if there is no user then stop iteration
        if len(subscriber_emails) == 0:
            print("No user found.")
            return 

        # if there is no batch size specified
        # by the user send all in one batch
        if not self.batch_size or self.batch_size <= 0:
            self.batch_size = len(subscriber_emails)

        print("Batch size for sending emails is set to %s" % self.batch_size)

        for i in range(0, len(subscriber_emails), self.batch_size):
            users = subscriber_emails[i : i + self.batch_size]

            for user in users:
                rendered_newsletter, created = self._render_newsletter(alert, user)
                if created:
                    pass
                yield rendered_newsletter, self._generate_email_message(
                    user.email, rendered_newsletter
                )

            # yield map(
            #     lambda user: self._generate_email_message(
            #         user.email, self._render_newsletter(alert, user)
            #     ),
            #     users,
            # )

    def send_emails(self):
        """sends newsletter emails to subscribers"""
        for alert in self.alerts:
            # issue_number = newsletter.issue.issue_number
            # this is used to calculate how many emails were
            # sent for each newsletter
            sent_emails = 0

            print("Ready to send newsletter for ALERT # %s" % alert.id)

            for newsletter, email_messages in self._get_batch_email_messages(alert):
                try:
                    messages = list(email_messages)
                except:
                    messages = [email_messages]

                try:
                    # send mass email with one connection open
                    sent = self.connection.send_messages(messages)
                    
                    print(
                        "Sent %s newsletters in one batch for ALERT # %s" % (len(messages), alert.id)
                    )

                    sent_emails += sent
                except Exception as e:
                    # create a new connection on error
                    self.connection = get_connection()
                    print(
                        "An error occurred while sending "
                        "newsletters for ALERT # %s "
                        "EXCEPTION: %s"
                        % (alert.id, e)
                    )
                finally:
                    # Wait sometime before sending next batch
                    # this is to prevent server overload
                    print(
                        "Waiting %s seconds before sending "
                        "next batch of newsletter for ALERT # %s"
                        "Schedule %s"
                        % (self.per_batch_wait, alert.id, self.schedule)
                    )
                    time.sleep(self.per_batch_wait)

                if sent > 0:
                    self.sent_newsletters.append(newsletter.id)

                print(
                    "Successfully Sent %s email(s) for NEWSLETTER # %s "
                    % (sent, newsletter.id)
                )

            if sent_emails > 0:
                self.sent_alerts.append(alert.id)

            print(
                "Successfully Sent %s email(s) for ALERT # %s "
                % (sent_emails, alert.id)
            )

        # Save newsletters to sent state
        Newsletter.objects.filter(id__in=self.sent_newsletters).update(
            is_sent=True, sent_at=datetime.now()
        )

        print(
            "Newsletter sending process completed. "
            "Successfully sent alert newsletters with ID %s"
            % self.sent_newsletters
        )


def send_email_newsletter(
    alerts: List[Alert] = None, schedule: Schedule = Schedule.DAILY
):
    print(f"About to send out alerts newsletter for {schedule} schedule")
    send_newsletter = NewsletterEmailSender(alerts=alerts, schedule=schedule)
    send_newsletter.send_emails()
    print(f"Successfully sent out alert newsletters for {schedule} schedule")
