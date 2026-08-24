import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class MercadoPagoError(Exception):
    pass


@dataclass(frozen=True)
class PixPayment:
    payment_id: str
    pix_code: str
    qr_code: str
    expires_at: datetime


class MercadoPagoClient:
    def __init__(self):
        if not settings.MERCADO_PAGO_ACCESS_TOKEN:
            raise ImproperlyConfigured("Configure MERCADO_PAGO_ACCESS_TOKEN.")
        self.base_url = settings.MERCADO_PAGO_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    def _request(self, method, path, *, payload=None, idempotency_key=None):
        headers = dict(self.headers)
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                json=payload,
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise MercadoPagoError("O Mercado Pago não concluiu a operação.") from exc

    def create_pix(self, invoice, token):
        expiration = datetime.combine(
            invoice.due_on, datetime.max.time(), tzinfo=UTC
        )
        row = self._request(
            "POST",
            "/v1/payments",
            payload={
                "transaction_amount": float(Decimal(invoice.total)),
                "description": f"Fatura {invoice.number}",
                "payment_method_id": "pix",
                "external_reference": f"invoice:{invoice.pk}",
                "date_of_expiration": expiration.isoformat(),
                "payer": {"email": invoice.client.email},
                "metadata": {"invoice_id": invoice.pk, "public_token": str(token)},
            },
            idempotency_key=f"devflow-invoice-pix-{invoice.pk}-{token}",
        )
        transaction = (row.get("point_of_interaction") or {}).get(
            "transaction_data"
        ) or {}
        pix_code = transaction.get("qr_code")
        qr_base64 = transaction.get("qr_code_base64")
        if not row.get("id") or not pix_code or not qr_base64:
            raise MercadoPagoError("O Mercado Pago não retornou os dados do Pix.")
        raw_expiration = row.get("date_of_expiration")
        return PixPayment(
            payment_id=str(row["id"]),
            pix_code=pix_code,
            qr_code=f"data:image/png;base64,{qr_base64}",
            expires_at=(
                datetime.fromisoformat(raw_expiration.replace("Z", "+00:00"))
                if raw_expiration
                else expiration
            ),
        )

    def create_subscription(self, subscription, back_url):
        return self._request(
            "POST",
            "/preapproval",
            payload={
                "reason": "DevFlow Pro",
                "external_reference": f"subscription:{subscription.organization_id}",
                "payer_email": subscription.organization.owner.email,
                "back_url": back_url,
                "status": "pending",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": 25.0,
                    "currency_id": "BRL",
                },
            },
        )

    def update_subscription(self, subscription_id, status):
        return self._request(
            "PUT", f"/preapproval/{subscription_id}", payload={"status": status}
        )

    def get_payment(self, payment_id):
        return self._request("GET", f"/v1/payments/{payment_id}")

    def get_subscription(self, subscription_id):
        return self._request("GET", f"/preapproval/{subscription_id}")

    def get_authorized_payment(self, payment_id):
        return self._request("GET", f"/authorized_payments/{payment_id}")

    def cancel_payment(self, payment_id):
        return self._request(
            "PUT", f"/v1/payments/{payment_id}", payload={"status": "cancelled"}
        )

    def refund_payment(self, payment_id, amount=None):
        payload = {"amount": float(Decimal(amount))} if amount is not None else {}
        return self._request(
            "POST",
            f"/v1/payments/{payment_id}/refunds",
            payload=payload,
            idempotency_key=f"devflow-refund-{payment_id}-{amount or 'full'}",
        )

    @staticmethod
    def verify_webhook(data_id, x_request_id, x_signature):
        secret = settings.MERCADO_PAGO_WEBHOOK_SECRET
        if not secret:
            raise ImproperlyConfigured("Configure MERCADO_PAGO_WEBHOOK_SECRET.")
        parts = {}
        for item in x_signature.split(","):
            key, separator, value = item.strip().partition("=")
            if separator:
                parts[key] = value
        timestamp = parts.get("ts")
        received = parts.get("v1")
        if not timestamp or not received or not data_id or not x_request_id:
            return False
        manifest = f"id:{str(data_id).lower()};request-id:{x_request_id};ts:{timestamp};"
        expected = hmac.new(
            secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, received)
