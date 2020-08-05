from django.contrib import admin

from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'default_account')


admin.site.register(Customer, CustomerAdmin)
