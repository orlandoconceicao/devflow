from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from .models import Invoice, InvoicePayment, InvoicePaymentEvent, Revenue


class PaymentProviderError(Exception):
    pass


@dataclass(frozen=True)
class PixResult:
    provider_payment_id: str
    pix_code: str
    qr_code_url: str
    expires_at: datetime


class StripePixProvider:
    def __init__(self):
        if settings.PAYMENT_PROVIDER != "stripe" or not settings.PAYMENT_API_KEY:
            raise ImproperlyConfigured("Configure PAYMENT_PROVIDER=stripe e PAYMENT_API_KEY.")
        import stripe

        self.stripe = stripe
        stripe.api_key = settings.PAYMENT_API_KEY

    def create(self, invoice, token):
        amount = int(
            (Decimal(invoice.total) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        try:
            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency="brl",
                payment_method_types=["pix"],
                payment_method_data={"type": "pix"},
                payment_method_options={
                    "pix": {"expires_after_seconds": settings.PIX_EXPIRATION_SECONDS}
                },
                confirm=True,
                description=f"Fatura {invoice.number}",
                metadata={"invoice_id": str(invoice.pk), "public_token": str(token)},
                idempotency_key=f"devflow-invoice-pix-{invoice.pk}-{token}",
            )
            qr = intent.next_action.pix_display_qr_code
            return PixResult(
                provider_payment_id=intent.id,
                pix_code=qr.data,
                qr_code_url=qr.image_url_png,
                expires_at=datetime.fromtimestamp(qr.expires_at, tz=UTC),
            )
        except Exception as exc:
            raise PaymentProviderError("Não foi possível gerar a cobrança Pix.") from exc

    def parse_webhook(self, payload, signature):
        if not settings.PIX_WEBHOOK_SECRET:
            raise ImproperlyConfigured("Configure PIX_WEBHOOK_SECRET.")
        return self.stripe.Webhook.construct_event(
            payload, signature, settings.PIX_WEBHOOK_SECRET
        )


def get_pix_provider():
    return StripePixProvider()


@transaction.atomic
def generate_pix(invoice, *, regenerate=False, provider=None):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status in (Invoice.Status.PAID, Invoice.Status.CANCELLED):
        raise PaymentProviderError("Esta fatura não aceita uma nova cobrança.")
    current = invoice.payments.filter(status=InvoicePayment.Status.PENDING).first()
    if current and current.expires_at > timezone.now() and not regenerate:
        return current
    if current:
        current.status = InvoicePayment.Status.EXPIRED
        current.save(update_fields=["status", "updated_at"])
    if invoice.total <= 0:
        raise PaymentProviderError("A cobrança deve possuir valor maior que zero.")

    import uuid

    token = uuid.uuid4()
    result = (provider or get_pix_provider()).create(invoice, token)
    payment = InvoicePayment.objects.create(
        invoice=invoice,
        public_token=token,
        provider_payment_id=result.provider_payment_id,
        amount=invoice.total,
        pix_code=result.pix_code,
        qr_code_url=result.qr_code_url,
        expires_at=result.expires_at,
    )
    if invoice.status == Invoice.Status.DRAFT:
        invoice.status = Invoice.Status.SENT
        invoice.save(update_fields=["status"])
    from .tasks import deliver_invoice_payment

    transaction.on_commit(lambda: deliver_invoice_payment.delay(payment.id))
    return payment


@transaction.atomic
def process_stripe_event(event):
    event_id = event["id"]
    event_type = event["type"]
    intent = event["data"]["object"]
    payment = (
        InvoicePayment.objects.select_for_update()
        .select_related("invoice", "invoice__organization", "invoice__client")
        .filter(provider_payment_id=intent.get("id"))
        .first()
    )
    _, event_created = InvoicePaymentEvent.objects.get_or_create(
        provider_event_id=event_id,
        defaults={"event_type": event_type, "payment": payment},
    )
    if not event_created:
        return "duplicate"
    if not payment:
        return "ignored"
    if event_type == "payment_intent.succeeded":
        expected = int((payment.amount * 100).quantize(Decimal("1")))
        received = intent.get("amount_received", intent.get("amount"))
        if received != expected or str(intent.get("currency", "")).lower() != "brl":
            raise PaymentProviderError("Valor ou moeda divergente no webhook.")
        if payment.status != InvoicePayment.Status.PAID:
            now = timezone.now()
            payment.status = InvoicePayment.Status.PAID
            payment.paid_at = now
            payment.save(update_fields=["status", "paid_at", "updated_at"])
            invoice = payment.invoice
            invoice.status = Invoice.Status.PAID
            invoice.paid_at = now
            invoice.save(update_fields=["status", "paid_at"])
            Revenue.objects.get_or_create(
                invoice=invoice,
                defaults={
                    "organization": invoice.organization,
                    "project": invoice.project,
                    "client": invoice.client,
                    "description": f"Pagamento da fatura {invoice.number}",
                    "amount": payment.amount,
                    "occurred_on": timezone.localdate(),
                    "created_by": invoice.created_by,
                },
            )
        return "paid"
    if event_type in ("payment_intent.payment_failed", "payment_intent.canceled"):
        if payment.status != InvoicePayment.Status.PAID:
            payment.status = (
                InvoicePayment.Status.EXPIRED
                if event_type == "payment_intent.canceled"
                else InvoicePayment.Status.FAILED
            )
            payment.save(update_fields=["status", "updated_at"])
        return "failed"
    return "ignored"
