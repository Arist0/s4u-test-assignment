import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from transfer.models import ScheduledPayment, InsufficientFunds

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run scheduled payments'

    def add_arguments(self, parser):
        parser.add_argument('--process-overdue', action='store_true', help="Include overdue payments to queue")

    def handle(self, *args, **options):
        today = datetime.now().date()
        if options['process_overdue']:
            scheduled_payments = ScheduledPayment.objects.filter(scheduled_date__lte=today, transfer__isnull=True)
        else:
            scheduled_payments = ScheduledPayment.objects.filter(scheduled_date=today, transfer__isnull=True)

        for schedule in scheduled_payments:
            try:
                schedule.run_scheduled_payment()
            except InsufficientFunds:
                pass
