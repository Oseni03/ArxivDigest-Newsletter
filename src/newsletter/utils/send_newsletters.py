import logging
import time
from typing import List

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Schedule, Subscription
from newsletter.models import Newsletter, Paper, PaperTopic

User = get_user_model()


logger = logging.getLogger(__name__)


class NewsletterEmailSender:
    """The main class that handles sending email newsletters"""

    def __init__(
        self, topics: List[PaperTopic] = None, schedule: Schedule = None
    ):
        self.topics = self._get_topics(topics=topics)
        # Schedule
        self.schedule = schedule
        # Size of each batch to be sent
        self.batch_size = settings.NEWSLETTER_EMAIL_BATCH_SIZE
        # list of topics that were sent
        self.sent_topics = []
        # Waiting time after each batch (in seconds)
        self.per_batch_wait = settings.NEWSLETTER_EMAIL_BATCH_WAIT
        # connection to the server
        self.connection = get_connection()
        self.email_host_user = settings.EMAIL_HOST_USER

    @staticmethod
    def _get_topics(topics=None):
        """
        gets topics to be sent

        :param topics: Newsletter QuerySet
        :param schedule: Subscription.Schedule instance
            will not be sent
        """

        if topics is None:
            topics = PaperTopic.objects.all()

        return topics

    @staticmethod
    def _render_newsletter(topic: PaperTopic, user):
        """renders newsletter template and returns Newsletter object"""
        subject = f"ArxivDigest - {topic.name}"
        papers = Paper.objects.filter(topics=topic, is_visible=True)

        context = {
            "topic": topic,
            "papers": papers,
            "unsubscribe_url": reverse("accounts:unsubscribe", args=(user.id,)),
            "site_url": settings.NEWSLETTER_SITE_BASE_URL,
        }

        html = render_to_string("newsletter/email/newsletter_email.html", context)

        rendered_newsletter = Newsletter.objects.create(
            topic=topic,
            subject=subject,
            content=html,
        )

        return rendered_newsletter

    def _generate_email_message(self, to_email, rendered_newsletter):
        """
        Generates email message for an email_address

        :param to_email: user email address
        :param rendered_newsletter: rendered html of the newsletter with subject
        """
        message = EmailMessage(
            subject=rendered_newsletter.get("subject"),
            body=rendered_newsletter.get("html"),
            from_email=self.email_host_user,
            to=[to_email],
            connection=self.connection,
        )
        message.content_subtype = "html"

        return message

    def _get_batch_email_messages(self, topic: PaperTopic):
        """
        Yields EmailMessage list in batches

        :param topic: PaperTopic object/instance
        """

        subscriber_emails = User.objects.filter(
            subscriptions__topic=topic, subscriptions__schedule=self.schedule
        )

        # if there is no user then stop iteration
        if len(subscriber_emails) == 0:
            logger.info("No user found.")
            return

        # if there is no batch size specified
        # by the user send all in one batch
        if not self.batch_size or self.batch_size <= 0:
            self.batch_size = len(subscriber_emails)

        logger.info("Batch size for sending emails is set to %s", self.batch_size)

        for i in range(0, len(subscriber_emails), self.batch_size):
            users = subscriber_emails[i : i + self.batch_size]

            yield map(
                lambda user: self._generate_email_message(
                    user.email, self._render_newsletter(topic, user)
                ),
                users,
            )

    def send_emails(self):
        """sends newsletter emails to subscribers"""
        for topic in self.topics:
            # issue_number = newsletter.issue.issue_number
            # this is used to calculate how many emails were
            # sent for each newsletter
            sent_emails = 0

            logger.info("Ready to send newsletter for TOPIC # %s", topic.abbrv)

            for email_messages in self._get_batch_email_messages(topic):
                messages = list(email_messages)

                try:
                    # send mass email with one connection open
                    sent = self.connection.send_messages(messages)

                    logger.info(
                        "Sent %s newsletters in one batch for TOPIC # %s",
                        len(messages),
                        topic.abbrv,
                    )

                    sent_emails += sent
                except Exception as e:
                    # create a new connection on error
                    self.connection = get_connection()
                    logger.error(
                        "An error occurred while sending "
                        "newsletters for TOPIC # %s "
                        "EXCEPTION: %s",
                        topic.abbrv,
                        e,
                    )
                finally:
                    # Wait sometime before sending next batch
                    # this is to prevent server overload
                    logger.info(
                        "Waiting %s seconds before sending "
                        "next batch of newsletter for ISSUE # %s"
                        "Schedule %s",
                        self.per_batch_wait,
                        self.schedule,
                        topic.abbrv,
                    )
                    time.sleep(self.per_batch_wait)

            if sent_emails > 0:
                self.sent_topics.append(topic.abbrv)

            logger.info(
                "Successfully Sent %s email(s) for TOPIC # %s ",
                sent_emails,
                topic.abbrv,
            )

        # Save newsletters to sent state
        # Newsletter.objects.filter(
        #     id__in=self.sent_topics
        # ).update(is_sent=True, sent_at=timezone.now())

        logger.info(
            "Newsletter sending process completed. "
            "Successfully sent newsletters with ID %s",
            self.sent_topics,
        )


def send_email_newsletter(
    topics: List[PaperTopic] = None, schedule: Schedule = Schedule.DAILY
):
    logger.info(f"About to send out newsletter for {schedule} schedule")
    send_newsletter = NewsletterEmailSender(topics=topics, schedule=schedule)
    send_newsletter.send_emails()
    logger.info(f"Successfully sent out newsletters for {schedule} schedule")
