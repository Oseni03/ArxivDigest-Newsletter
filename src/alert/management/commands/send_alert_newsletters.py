from django.core.management.base import BaseCommand, CommandError, CommandParser

from accounts.models import Schedule
from alert.utils import send_email_newsletter


class Command(BaseCommand):
    help ="Send alert newsletter for the specified schedule"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("schedule", type=str)
        return super().add_arguments(parser)
    
    def handle(self, *args, **options):
        schedule = options["schedule"]
        try:
            send_email_newsletter(schedule=schedule)
        except Exception as e:
            raise CommandError(f"Schedule {schedule} raised '{e}' error")
        
        self.style.SUCCESS("Successfully sent out alert newsletters for '%s' schedule" % schedule)