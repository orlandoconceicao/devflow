import hashlib
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.payments.mercado_pago import MercadoPagoClient, MercadoPagoError
from apps.work.context import current_membership
from apps.finance.payments import PaymentProviderError, process_mercado_pago_payment

from .models import PaymentEvent, Plan, Subscription, SubscriptionPayment
from .policy import SubscriptionPolicy
from .providers import get_subscription_service
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
            organization__memberships__user=self.request.user,
            organization__memberships__is_active=True,
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
@transaction.atomic
def checkout(request):
    org = owner_org(request)
    s = Subscription.objects.select_for_update().get(organization=org)
    Plan.objects.get(slug="pro", price="25.00")
    return Response(get_subscription_service().create_checkout(s))


@api_view(["POST"])
def cancel(request):
    org = owner_org(request)
    if not org.subscription.provider_subscription_id:
        return Response({"detail": "Assinatura externa não encontrada."}, status=409)
    get_subscription_service().cancel(org.subscription)
    org.subscription.status = Subscription.Status.CANCELED
    org.subscription.cancel_at_period_end = False
    org.subscription.canceled_at = timezone.now()
    org.subscription.save(
        update_fields=["status", "cancel_at_period_end", "canceled_at", "updated_at"]
    )
    return Response(SubscriptionSerializer(org.subscription).data)


def _subscription_from_resource(resource):
    external_reference = str(resource.get("external_reference", ""))
    if external_reference.startswith("subscription:"):
        return Subscription.objects.select_for_update().filter(
            organization_id=external_reference.partition(":")[2]
        ).first()
    subscription_id = resource.get("preapproval_id") or resource.get("id")
    return Subscription.objects.select_for_update().filter(
        provider_subscription_id=str(subscription_id)
    ).first()


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def mercado_pago_webhook(request):
    data_id = request.query_params.get("data.id") or (request.data.get("data") or {}).get("id")
    request_id = request.headers.get("X-Request-Id", "")
    signature = request.headers.get("X-Signature", "")
    try:
        if not MercadoPagoClient.verify_webhook(data_id, request_id, signature):
            raise ValueError
    except Exception:
        return Response({"detail": "Assinatura inválida."}, status=400)
    topic = request.data.get("type") or request.query_params.get("type", "")
    client = MercadoPagoClient()
    try:
        if topic == "payment":
            resource = client.get_payment(data_id)
            if str(resource.get("external_reference", "")).startswith("invoice:"):
                marker = resource.get("date_last_updated") or resource.get("status")
                result = process_mercado_pago_payment(
                    resource, f"payment:{data_id}:{marker}"
                )
                return Response({"received": True, "result": result})
        elif topic == "subscription_preapproval":
            resource = client.get_subscription(data_id)
        elif topic == "subscription_authorized_payment":
            resource = client.get_authorized_payment(data_id)
        else:
            return Response({"received": True, "result": "ignored"})
    except (MercadoPagoError, PaymentProviderError) as exc:
        return Response({"detail": str(exc)}, status=400)

    event_type = str(resource.get("status", topic))
    event_id = f"{topic}:{data_id}:{resource.get('last_modified') or event_type}"
    with transaction.atomic():
        subscription = _subscription_from_resource(resource)
        row, created = PaymentEvent.objects.get_or_create(
            provider_event_id=event_id,
            defaults={
                "provider": "mercado_pago",
                "event_type": event_type,
                "payload_hash": hashlib.sha256(request.body).hexdigest(),
                "organization_id": subscription.organization_id if subscription else None,
            },
        )
        if not created:
            return Response({"received": True, "duplicate": True})
        if subscription:
            pro = Plan.objects.get(slug="pro", price="25.00")
            if topic == "subscription_preapproval":
                subscription.provider = "mercado_pago"
                subscription.provider_subscription_id = str(resource["id"])
                subscription.provider_payer_id = str(resource.get("payer_id", ""))
                if event_type == "authorized":
                    subscription.plan = pro
                    subscription.status = Subscription.Status.ACTIVE
                elif event_type in ("cancelled", "paused"):
                    subscription.status = Subscription.Status.CANCELED
                    subscription.canceled_at = timezone.now()
            elif topic == "subscription_authorized_payment":
                if Decimal(str(resource.get("transaction_amount", 0))) != pro.price or resource.get("currency_id") != "BRL":
                    return Response(
                        {"detail": "Valor ou moeda não corresponde ao plano Pro."},
                        status=400,
                    )
                subscription.plan = pro
                subscription.status = Subscription.Status.ACTIVE
                SubscriptionPayment.objects.update_or_create(
                    provider_payment_id=str(resource["id"]),
                    defaults={
                        "subscription": subscription,
                        "amount": "25.00",
                        "currency": "BRL",
                        "status": "PAID" if event_type == "approved" else "FAILED",
                        "paid_at": timezone.now(),
                    },
                )
            subscription.save()
            row.processed = True
            row.processed_at = timezone.now()
            row.save(update_fields=["processed", "processed_at"])
    return Response({"received": True})
