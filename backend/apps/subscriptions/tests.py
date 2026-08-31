import hashlib
import hmac
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership
from apps.organizations.services import create_organization
from apps.payments.mercado_pago import MercadoPagoClient

from .models import Plan


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


class BillingPermissionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.free = Plan.objects.create(slug="free", name="Free", price="0.00")
        cls.pro = Plan.objects.create(slug="pro", name="Pro", price="25.00")
        cls.owner = User.objects.create_user(
            email="billing-owner@example.test", password="StrongPass!2026"
        )
        cls.member = User.objects.create_user(
            email="billing-member@example.test", password="StrongPass!2026"
        )
        cls.other_owner = User.objects.create_user(
            email="billing-other@example.test", password="StrongPass!2026"
        )
        cls.organization = create_organization(user=cls.owner, name="Billing A")
        cls.other_organization = create_organization(
            user=cls.other_owner, name="Billing B"
        )
        OrganizationMembership.objects.create(
            organization=cls.organization,
            user=cls.member,
            role=OrganizationMembership.Role.MEMBER,
        )

    def headers(self, organization):
        return {"HTTP_X_ORGANIZATION_ID": str(organization.id)}

    def test_owner_can_read_billing_and_member_cannot_manage_it(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.get(
                "/api/billing/subscription/", **self.headers(self.organization)
            ).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(
                "/api/billing/payments/", **self.headers(self.organization)
            ).status_code,
            status.HTTP_200_OK,
        )

        self.client.force_authenticate(self.member)
        for method, path in (
            (self.client.get, "/api/billing/subscription/"),
            (self.client.get, "/api/billing/payments/"),
            (self.client.post, "/api/billing/checkout/"),
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    method(path, **self.headers(self.organization)).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_owner_cannot_switch_to_another_tenant_with_header(self):
        self.client.force_authenticate(self.owner)
        for path in (
            "/api/billing/subscription/",
            "/api/billing/payments/",
            "/api/billing/checkout/",
        ):
            with self.subTest(path=path):
                method = self.client.post if path.endswith("checkout/") else self.client.get
                self.assertEqual(
                    method(path, **self.headers(self.other_organization)).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
