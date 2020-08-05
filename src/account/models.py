from django.db import models


class Account(models.Model):
    # TODO: replace number with UUIDField
    # TODO: add currency field as ForeignKey to a new model named Currency
    number = models.PositiveIntegerField(unique=True)
    owner = models.ForeignKey('customer.Customer', models.CASCADE)
    balance = models.DecimalField(default=0, max_digits=18, decimal_places=2)

    def __str__(self):
        return f"{self.number}: {self.balance}"


# TODO add Currency model, e.g. name, short_name, symbol
