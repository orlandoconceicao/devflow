import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.payments.mercado_pago import MercadoPagoClient, MercadoPagoError

from .models import Invoice, InvoicePayment, InvoicePaymentEvent, Revenue


class PaymentProviderError(Exception):
    pass


@dataclass(frozen=True)
class PixResult:
    provider_payment_id: str
    pix_code: str
    qr_code: str
    expires_at: datetime


class MercadoPagoPixService:
    def __init__(self, client=None):
        self.client = client or MercadoPagoClient()

    def create(self, invoice, token):
        try:
            result = self.client.create_pix(invoice, token)
        except MercadoPagoError as exc:
            raise PaymentProviderError(
                "Não foi possível gerar a cobrança Pix."
            ) from exc
        return PixResult(
            provider_payment_id=result.payment_id,
            pix_code=result.pix_code,
            qr_code=result.qr_code,
            expires_at=result.expires_at,
        )


def get_pix_service():
    return MercadoPagoPixService()


@transaction.atomic
def generate_pix(invoice, *, regenerate=False, service=None):
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

    attempt = invoice.payments.count() + 1
    token = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"{settings.SECRET_KEY}:invoice:{invoice.pk}:attempt:{attempt}",
    )
    result = (service or get_pix_service()).create(invoice, token)
    payment = InvoicePayment.objects.create(
        invoice=invoice,
        public_token=token,
        provider_payment_id=result.provider_payment_id,
        amount=invoice.total,
        pix_code=result.pix_code,
        qr_code=result.qr_code,
        expires_at=result.expires_at,
    )
    if invoice.status == Invoice.Status.DRAFT:
        invoice.status = Invoice.Status.SENT
        invoice.save(update_fields=["status"])
    from .tasks import deliver_invoice_payment

    transaction.on_commit(lambda: deliver_invoice_payment.delay(payment.id))
    return payment


@transaction.atomic
def process_mercado_pago_payment(payment_data, event_id):
    payment = (
        InvoicePayment.objects.select_for_update()
        .select_related("invoice", "invoice__organization", "invoice__client")
        .filter(provider_payment_id=str(payment_data.get("id")))
        .first()
    )
    event_type = str(payment_data.get("status", "unknown"))
    _, created = InvoicePaymentEvent.objects.get_or_create(
        provider_event_id=event_id,
        defaults={"event_type": event_type, "payment": payment},
    )
    if not created:
        return "duplicate"
    if not payment:
        return "ignored"
    if payment_data.get("external_reference") != f"invoice:{payment.invoice_id}":
        raise PaymentProviderError("Referência externa divergente no webhook.")
    if event_type == "approved":
        amount = Decimal(str(payment_data.get("transaction_amount", "0")))
        if amount != payment.amount or payment_data.get("currency_id") != "BRL":
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
    status_map = {
        "cancelled": InvoicePayment.Status.CANCELLED,
        "rejected": InvoicePayment.Status.FAILED,
        "refunded": InvoicePayment.Status.CANCELLED,
        "charged_back": InvoicePayment.Status.FAILED,
    }
    if event_type in status_map and payment.status != InvoicePayment.Status.PAID:
        payment.status = status_map[event_type]
        payment.save(update_fields=["status", "updated_at"])
        return "failed"
    return "ignored"
