from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseViewSet,
    InvoiceViewSet,
    MemberRateViewSet,
    RevenueViewSet,
    TimeEntryViewSet,
    export_hours,
    finance_dashboard,
    reports,
    public_payment,
    stripe_invoice_webhook,
)

router = DefaultRouter()
router.register("time-entries", TimeEntryViewSet, basename="time-entry")
router.register("member-rates", MemberRateViewSet, basename="member-rate")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("revenues", RevenueViewSet, basename="revenue")
router.register("invoices", InvoiceViewSet, basename="invoice")
urlpatterns = [
    path("", include(router.urls)),
    path("finance/dashboard/", finance_dashboard),
    path("reports/", reports),
    path("reports/hours/export/", export_hours),
    path("public/payments/<uuid:token>/", public_payment),
    path("webhooks/payments/stripe/invoices/", stripe_invoice_webhook),
]
