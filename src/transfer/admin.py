from django.contrib import admin

from transfer.models import Transfer, ScheduledPayment


class TransferAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'from_account', 'to_account', 'amount')
    readonly_fields = ('created_at', 'from_account', 'to_account', 'amount')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ScheduledPaymentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'from_account', 'to_account', 'amount', 'scheduled_date', 'is_paid')
    readonly_fields = ('transfer', )


admin.site.register(Transfer, TransferAdmin)
admin.site.register(ScheduledPayment, ScheduledPaymentAdmin)
