from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.core.management import call_command

from django.test import TestCase

from account.models import Account
from customer.models import Customer
from transfer.models import Transfer, ScheduledPayment, InvalidAmount, InsufficientFunds, InvalidAccounts, \
    InvalidScheduledDate


class TransferTest(TestCase):
    def setUp(self):
        super(TransferTest, self).setUp()

        customer = Customer.objects.create(
            email='test@test.invalid',
            full_name='Test Customer',
        )

        self.account1 = Account.objects.create(number=123, owner=customer, balance=1000)
        self.account2 = Account.objects.create(number=456, owner=customer, balance=1000)

    def test_basic_transfer(self):
        Transfer.do_transfer(self.account1, self.account2, 100)

        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, 900)
        self.assertEqual(self.account2.balance, 1100)
        self.assertTrue(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
        ).exists())

    def test_invalid_accounts_transfer(self):
        with self.assertRaises(InvalidAccounts):
            Transfer.do_transfer(None, None, 100)
        with self.assertRaises(InvalidAccounts):
            Transfer.do_transfer(None, self.account2, 100)
        with self.assertRaises(InvalidAccounts):
            Transfer.do_transfer(self.account1, None, 100)
        with self.assertRaises(InvalidAccounts):
            Transfer.do_transfer(self.account1, self.account1, 100)

        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, 1000)
        self.assertEqual(self.account2.balance, 1000)
        self.assertFalse(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
        ).exists())

    def test_incorrect_amount_transfer(self):
        with self.assertRaises(InvalidAmount):
            Transfer.do_transfer(self.account1, self.account2, 0)

        with self.assertRaises(InvalidAmount):
            Transfer.do_transfer(self.account1, self.account2, -10)

        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, 1000)
        self.assertEqual(self.account2.balance, 1000)
        self.assertFalse(Transfer.objects.filter(
            amount__lte=0,
        ).exists())

    def test_insufficient_funds_transfer(self):
        with self.assertRaises(InsufficientFunds):
            Transfer.do_transfer(self.account1, self.account2, 10000)

        Transfer.do_transfer(self.account1, self.account2, 1000)

        self.account1.refresh_from_db()
        self.account2.refresh_from_db()

        self.assertEqual(self.account1.balance, 0)
        self.assertEqual(self.account2.balance, 2000)
        self.assertTrue(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=1000,
        ).exists())


class ScheduledPaymentsTest(TestCase):
    def setUp(self):
        super(ScheduledPaymentsTest, self).setUp()

        customer = Customer.objects.create(
            email='test-sp@test.invalid',
            full_name='Test Scheduled Payments',
        )

        self.account1 = Account.objects.create(number=321, owner=customer, balance=1000)
        self.account2 = Account.objects.create(number=654, owner=customer, balance=1000)
        self.today = datetime.now().date()
        self.tomorrow = self.today + relativedelta(days=1)
        self.yesterday = self.today - relativedelta(days=1)

    def test_schedule_payment_without_date(self):
        scheduled_payment = ScheduledPayment.schedule_payment(from_account=self.account1,
                                                              to_account=self.account2,
                                                              amount=100)
        self.assertTrue(ScheduledPayment.objects.filter(from_account=self.account1,
                                                        to_account=self.account2,
                                                        amount=100,
                                                        scheduled_date=self.today).exists())
        self.assertEqual(scheduled_payment.scheduled_date, self.today)

    def test_schedule_payment(self):
        scheduled_payment = ScheduledPayment.schedule_payment(from_account=self.account1,
                                                              to_account=self.account2,
                                                              amount=100,
                                                              scheduled_date=self.tomorrow)
        self.assertTrue(ScheduledPayment.objects.filter(from_account=self.account1,
                                                        to_account=self.account2,
                                                        amount=100,
                                                        scheduled_date=self.tomorrow).exists())
        self.assertEqual(scheduled_payment.scheduled_date, self.tomorrow)

    def test_schedule_payment_in_past(self):
        with self.assertRaises(InvalidScheduledDate):
            ScheduledPayment.schedule_payment(from_account=self.account1,
                                              to_account=self.account2,
                                              amount=100,
                                              scheduled_date=self.yesterday)
        self.assertFalse(ScheduledPayment.objects.filter(from_account=self.account1,
                                                         to_account=self.account2,
                                                         amount=100,
                                                         scheduled_date=self.yesterday).exists())

    def test_run_scheduled_payments_command(self):
        scheduled_payment = ScheduledPayment.schedule_payment(from_account=self.account1,
                                                              to_account=self.account2,
                                                              amount=100,
                                                              scheduled_date=self.today)
        call_command('run_scheduled_payments')
        scheduled_payment.refresh_from_db()
        self.assertNotEqual(scheduled_payment.transfer, None)
        self.assertTrue(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
        ).exists())
        self.assertTrue(ScheduledPayment.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
            scheduled_date=self.today + relativedelta(months=1)
        ).exists())
