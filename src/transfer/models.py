from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import F

from account.models import Account


class InvalidAccounts(Exception):
    pass


class InsufficientFunds(Exception):
    pass


class InvalidAmount(Exception):
    pass


class InvalidScheduledDate(Exception):
    pass


class Transfer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    @staticmethod
    def validate_transaction_params(from_account: Account, to_account: Account, amount: Decimal):
        if any([from_account is None,
                to_account is None,
                from_account == to_account]):
            raise InvalidAccounts()
        if amount <= 0:
            raise InvalidAmount()

    @staticmethod
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal):
        Transfer.validate_transaction_params(from_account, to_account, amount)
        is_updated = Account.objects.filter(
            id=from_account.id,
            balance__gte=amount
        ).update(balance=F('balance') - amount)

        if not is_updated:
            raise InsufficientFunds()

        to_account.balance = F('balance') + amount
        to_account.save()

        return Transfer.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )


class ScheduledPayment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    from_account = models.ForeignKey(Account, models.CASCADE, related_name='scheduled_transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='scheduled_transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    scheduled_date = models.DateField(blank=True)
    is_recurring = models.BooleanField(default=True)

    transfer = models.ForeignKey(Transfer, models.CASCADE, related_name='scheduled_by', null=True)

    @staticmethod
    def schedule_payment(from_account: Account, to_account: Account, amount: Decimal,
                         scheduled_date: Optional[date] = None, is_recurring: bool = True):
        Transfer.validate_transaction_params(from_account, to_account, amount)

        if scheduled_date and scheduled_date < datetime.now().date():
            raise InvalidScheduledDate()

        return ScheduledPayment.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            scheduled_date=scheduled_date if scheduled_date else datetime.now().date(),
            is_recurring=is_recurring
        )

    def run_scheduled_payment(self) -> None:
        self.transfer = Transfer.do_transfer(self.from_account,
                                             self.to_account,
                                             self.amount)
        self.save()
        if self.is_recurring:
            next_payment_date = self.scheduled_date + relativedelta(months=+1)
            ScheduledPayment.schedule_payment(self.from_account,
                                              self.to_account,
                                              self.amount,
                                              next_payment_date)

    @property
    def is_paid(self):
        return self.transfer is not None
