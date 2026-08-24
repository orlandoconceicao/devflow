from django.contrib import admin

from .models import (
    Expense,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    InvoicePaymentEvent,
    MemberRate,
    Revenue,
    TimeEntry,
)

admin.site.register([
    Expense, Invoice, InvoiceItem, InvoicePayment, InvoicePaymentEvent,
    MemberRate, Revenue, TimeEntry,
])
