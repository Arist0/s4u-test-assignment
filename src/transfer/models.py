from decimal import Decimal
from django.db import models
from django.db.models import F

from account.models import Account


class InvalidAccounts(Exception):
    pass


class InsufficientFunds(Exception):
    pass


class InvalidAmount(Exception):
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
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal) -> object:
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
