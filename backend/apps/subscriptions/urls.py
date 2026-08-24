from django.urls import path

from .views import (
    PlanListView,
    SubscriptionView,
    billing_payments,
    billing_subscription,
    billing_usage,
    cancel,
    checkout,
    mercado_pago_webhook,
)

urlpatterns = [
    path("plans/", PlanListView.as_view()),
    path("subscription/", SubscriptionView.as_view()),
    path("billing/subscription/", billing_subscription),
    path("billing/usage/", billing_usage),
    path("billing/payments/", billing_payments),
    path("billing/checkout/", checkout),
    path("billing/cancel/", cancel),
    path("webhooks/mercado-pago/", mercado_pago_webhook),
]
