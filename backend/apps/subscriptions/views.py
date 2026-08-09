import hashlib

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.work.context import current_membership

from .models import PaymentEvent, Plan, Subscription, SubscriptionPayment
from .policy import SubscriptionPolicy
from .providers import get_provider
from .serializers import PaymentSerializer, PlanSerializer, SubscriptionSerializer


class PlanListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PlanSerializer
    pagination_class = None
    queryset = Plan.objects.filter(is_active=True).order_by("price")


class SubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer

    def get_object(self):
        qs = Subscription.objects.filter(
            organization__memberships__user=self.request.user
        ).select_related("plan", "organization")
        organization_id = self.request.query_params.get("organization_id")
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        obj = qs.first()
        if not obj:
            raise NotFound("Assinatura não encontrada.")
        return obj


def owner_org(request):
    m = current_membership(request)
    if m.role != OrganizationMembership.Role.OWNER:
        raise PermissionDenied("Somente o proprietário pode gerenciar a assinatura.")
    return m.organization


@api_view(["GET"])
def billing_subscription(request):
    return Response(SubscriptionSerializer(owner_org(request).subscription).data)


@api_view(["GET"])
def billing_usage(request):
    return Response(
        SubscriptionPolicy(current_membership(request).organization).usage()
    )


@api_view(["GET"])
def billing_payments(request):
    return Response(
        PaymentSerializer(
            owner_org(request).subscription.payments.all().order_by("-created_at"),
            many=True,
        ).data
    )


@api_view(["POST"])
def checkout(request):
    org = owner_org(request)
    s = org.subscription
    pro = Plan.objects.get(slug="pro", price="25.00")
    return Response(
        get_provider().create_checkout(
            s,
            f"{__import__('django.conf',fromlist=['settings']).settings.FRONTEND_URL}/billing/success",
            f"{__import__('django.conf',fromlist=['settings']).settings.FRONTEND_URL}/billing/cancel",
        )
    )


@api_view(["POST"])
def billing_portal(request):
    org = owner_org(request)
    if not org.subscription.provider_customer_id:
        return Response({"detail": "Cliente de cobrança ainda não criado."}, status=409)
    from django.conf import settings

    return Response(
        get_provider().create_portal(
            org.subscription, f"{settings.FRONTEND_URL}/settings/billing"
        )
    )


@api_view(["POST"])
def cancel(request):
    org = owner_org(request)
    get_provider().cancel(org.subscription)
    org.subscription.cancel_at_period_end = True
    org.subscription.save(update_fields=["cancel_at_period_end"])
    return Response(SubscriptionSerializer(org.subscription).data)


@api_view(["POST"])
def reactivate(request):
    org = owner_org(request)
    get_provider().reactivate(org.subscription)
    org.subscription.cancel_at_period_end = False
    org.subscription.save(update_fields=["cancel_at_period_end"])
    return Response(SubscriptionSerializer(org.subscription).data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def payment_webhook(request, provider):
    if provider != "stripe":
        return Response(status=404)
    try:
        event = get_provider().verify_webhook(
            request.body, request.headers.get("Stripe-Signature", "")
        )
    except Exception:
        return Response({"detail": "Assinatura inválida."}, status=400)
    event = dict(event)
    event_id = event["id"]
    event_type = event["type"]
    obj = dict(event["data"]["object"])
    org_id = (obj.get("metadata") or {}).get("organization_id") or obj.get(
        "client_reference_id"
    )
    with transaction.atomic():
        row, created = PaymentEvent.objects.get_or_create(
            provider_event_id=event_id,
            defaults={
                "provider": "stripe",
                "event_type": event_type,
                "payload_hash": hashlib.sha256(request.body).hexdigest(),
                "organization_id": org_id,
            },
        )
        if not created:
            return Response({"received": True, "duplicate": True})
        subscription_ref = obj.get("subscription")
        s = (
            Subscription.objects.select_for_update()
            .filter(organization_id=org_id)
            .first()
            if org_id
            else Subscription.objects.select_for_update()
            .filter(provider_subscription_id=subscription_ref)
            .first()
        )
        if s:
            pro = Plan.objects.get(slug="pro", price="25.00")
            if event_type == "checkout.session.completed":
                s.provider = "stripe"
                s.provider_customer_id = obj.get("customer", "")
                s.provider_subscription_id = obj.get("subscription", "")
            elif event_type == "invoice.paid":
                if (
                    obj.get("amount_paid") != 2500
                    or str(obj.get("currency", "")).lower() != "brl"
                ):
                    return Response(
                        {"detail": "Valor ou moeda não corresponde ao plano Pro."},
                        status=400,
                    )
                s.plan = pro
                s.status = Subscription.Status.ACTIVE
                SubscriptionPayment.objects.update_or_create(
                    provider_payment_id=obj["id"],
                    defaults={
                        "subscription": s,
                        "amount": "25.00",
                        "currency": "BRL",
                        "status": "PAID",
                        "paid_at": timezone.now(),
                    },
                )
            elif event_type == "invoice.payment_failed":
                s.status = Subscription.Status.PAST_DUE
            elif event_type == "customer.subscription.deleted":
                s.status = Subscription.Status.CANCELED
                s.canceled_at = timezone.now()
            elif event_type == "customer.subscription.updated":
                s.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
            s.save()
            row.processed = True
            row.processed_at = timezone.now()
            row.save(update_fields=["processed", "processed_at"])
    return Response({"received": True})
