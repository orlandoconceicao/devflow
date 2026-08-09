from django.contrib import admin
from .models import Expense,Invoice,InvoiceItem,MemberRate,Revenue,TimeEntry
admin.site.register([Expense,Invoice,InvoiceItem,MemberRate,Revenue,TimeEntry])
