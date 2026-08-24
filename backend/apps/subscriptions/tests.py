import hashlib
import hmac
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.payments.mercado_pago import MercadoPagoClient


@override_settings(
    MERCADO_PAGO_ACCESS_TOKEN="test-token",
    MERCADO_PAGO_WEBHOOK_SECRET="test-webhook-secret",
    MERCADO_PAGO_BASE_URL="https://api.mercadopago.com",
)
class MercadoPagoClientTests(SimpleTestCase):
    def test_webhook_signature_uses_official_manifest(self):
        data_id = "12345"
        request_id = "request-123"
        timestamp = "1710000000"
        manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
        digest = hmac.new(
            b"test-webhook-secret", manifest.encode(), hashlib.sha256
        ).hexdigest()
        self.assertTrue(
            MercadoPagoClient.verify_webhook(
                data_id, request_id, f"ts={timestamp},v1={digest}"
            )
        )
        self.assertFalse(
            MercadoPagoClient.verify_webhook(
                data_id, request_id, f"ts={timestamp},v1=invalid"
            )
        )

    @patch("apps.payments.mercado_pago.requests.request")
    def test_pix_request_uses_idempotency_and_real_provider_data(self, request):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "id": 12345,
            "date_of_expiration": "2026-08-30T23:59:59+00:00",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "000201PIX",
                    "qr_code_base64": "dGVzdA==",
                }
            },
        }
        request.return_value = response
        invoice = Mock(
            pk=7,
            number="PIX-007",
            total="25.00",
            due_on=__import__("datetime").date(2026, 8, 30),
        )
        invoice.client.email = "payer@example.test"
        result = MercadoPagoClient().create_pix(invoice, "public-token")
        self.assertEqual(result.payment_id, "12345")
        self.assertEqual(result.pix_code, "000201PIX")
        self.assertTrue(result.qr_code.startswith("data:image/png;base64,"))
        headers = request.call_args.kwargs["headers"]
        self.assertEqual(
            headers["X-Idempotency-Key"],
            "devflow-invoice-pix-7-public-token",
        )
