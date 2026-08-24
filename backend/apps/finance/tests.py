from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership

from .models import Invoice, InvoicePayment, Revenue
from .payments import PaymentProviderError, PixResult, process_mercado_pago_payment


class FinanceApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)

    def login(self, user):
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "StrongPass!2026"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def setup_workspace(self):
        owner = User.objects.create_user(
            email="finance-owner@test.local", password="StrongPass!2026"
        )
        self.login(owner)
        organization = self.client.post(
            "/api/organizations/", {"name": "Finance Org"}, format="json"
        ).data
        headers = {"HTTP_X_ORGANIZATION_ID": str(organization["id"])}
        client = self.client.post(
            "/api/clients/", {"name": "Finance Client"}, format="json", **headers
        ).data
        project = self.client.post(
            "/api/projects/",
            {"name": "Finance Project", "client": client["id"], "status": "ACTIVE"},
            format="json",
            **headers,
        ).data
        return owner, organization, headers, client, project

    def test_finance_time_entries_invoices_reports_and_permissions(self):
        owner, organization, headers, client, project = self.setup_workspace()
        self.assertEqual(
            self.client.post(
                "/api/member-rates/",
                {"user": owner.id, "hourly_cost": "50.00", "hourly_rate": "100.00"},
                format="json",
                **headers,
            ).status_code,
            201,
        )
        timer = self.client.post(
            "/api/time-entries/start/",
            {"project": project["id"], "description": "Audit", "billable": True},
            format="json",
            **headers,
        )
        self.assertEqual(timer.status_code, 201)
        self.assertEqual(
            self.client.post(
                "/api/time-entries/start/",
                {"project": project["id"]},
                format="json",
                **headers,
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(
                f"/api/time-entries/{timer.data['id']}/stop/",
                {},
                format="json",
                **headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/expenses/",
                {
                    "project": project["id"],
                    "description": "Hosting",
                    "amount": "20.00",
                    "category": "SOFTWARE",
                    "occurred_on": "2026-08-23",
                },
                format="json",
                **headers,
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/api/revenues/",
                {
                    "project": project["id"],
                    "client": client["id"],
                    "description": "Project payment",
                    "amount": "200.00",
                    "occurred_on": "2026-08-23",
                },
                format="json",
                **headers,
            ).status_code,
            201,
        )
        invoice = self.client.post(
            "/api/invoices/",
            {
                "client": client["id"],
                "number": "INV-001",
                "issued_on": "2026-08-23",
                "due_on": "2026-08-30",
                "items": [
                    {
                        "description": "Development",
                        "quantity": "2",
                        "unit_price": "100.00",
                    }
                ],
            },
            format="json",
            **headers,
        )
        self.assertEqual(invoice.status_code, 201)
        self.assertEqual(invoice.data["total"], "200.00")
        paid = self.client.post(
            f"/api/invoices/{invoice.data['id']}/mark-paid/",
            {},
            format="json",
            **headers,
        )
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data["status"], "PAID")
        self.assertEqual(
            self.client.get("/api/finance/dashboard/", **headers).status_code, 200
        )
        self.assertEqual(self.client.get("/api/reports/", **headers).status_code, 200)
        export = self.client.get("/api/reports/hours/export/", **headers)
        self.assertEqual(export.status_code, 200)
        self.assertTrue(export["Content-Type"].startswith("text/csv"))

        member = User.objects.create_user(
            email="finance-member@test.local", password="StrongPass!2026"
        )
        OrganizationMembership.objects.create(
            organization_id=organization["id"], user=member, role="MEMBER"
        )
        self.login(member)
        self.assertEqual(
            self.client.get("/api/time-entries/", **headers).status_code, 200
        )
        self.assertEqual(self.client.get("/api/reports/", **headers).status_code, 200)
        self.assertEqual(
            self.client.get("/api/finance/dashboard/", **headers).status_code, 403
        )
        self.assertEqual(self.client.get("/api/expenses/", **headers).status_code, 403)


class PublicPixPaymentTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)
        cls.owner = User.objects.create_user(email="pix-owner@test.local", password="StrongPass!2026")
        cls.member = User.objects.create_user(email="pix-member@test.local", password="StrongPass!2026")
        cls.admin_user = User.objects.create_user(email="pix-admin@test.local", password="StrongPass!2026")

    def setUp(self):
        self.client.force_authenticate(self.owner)
        organization = self.client.post("/api/organizations/", {"name": "Pix Org"}, format="json").data
        self.headers = {"HTTP_X_ORGANIZATION_ID": str(organization["id"])}
        self.organization_id = organization["id"]
        self.customer = self.client.post("/api/clients/", {"name": "Cliente sem usuário"}, format="json", **self.headers).data
        self.invoice_data = {
            "client": self.customer["id"], "number": "PIX-001",
            "issued_on": "2026-08-23", "due_on": "2026-08-30",
            "payment_release_on": "2026-08-23", "items": [{"description": "Projeto", "quantity": "1", "unit_price": "1500.00"}],
        }

    def pix_result(self):
        return PixResult("mp_test_123", "000201PIXTEST", "data:image/png;base64,dGVzdA==", timezone.now() + timedelta(hours=1))

    def create_invoice(self):
        response = self.client.post("/api/invoices/", self.invoice_data, format="json", **self.headers)
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_only_owner_can_create_financial_records(self):
        self.assertEqual(self.create_invoice().data["total"], "1500.00")
        OrganizationMembership.objects.create(organization_id=self.organization_id, user=self.admin_user, role="ADMIN")
        self.client.force_authenticate(self.admin_user)
        admin_data = {**self.invoice_data, "number": "PIX-ADMIN"}
        self.assertEqual(self.client.post("/api/invoices/", admin_data, format="json", **self.headers).status_code, 403)
        OrganizationMembership.objects.create(organization_id=self.organization_id, user=self.member, role="MEMBER")
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post("/api/invoices/", self.invoice_data, format="json", **self.headers).status_code, 403)

    def test_invalid_amount_and_due_date_are_rejected(self):
        invalid = {**self.invoice_data, "number": "PIX-002", "due_on": "2026-08-22", "items": [{"description": "X", "quantity": "1", "unit_price": "0"}]}
        self.assertEqual(self.client.post("/api/invoices/", invalid, format="json", **self.headers).status_code, 400)

    @patch("apps.finance.payments.get_pix_service")
    def test_provider_creates_real_payload_and_generation_is_idempotent(self, provider_factory):
        provider_factory.return_value.create.return_value = self.pix_result()
        invoice = self.create_invoice()
        first = self.client.post(f"/api/invoices/{invoice.data['id']}/generate-payment/", {}, format="json", **self.headers)
        second = self.client.post(f"/api/invoices/{invoice.data['id']}/generate-payment/", {}, format="json", **self.headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["public_url"], second.data["public_url"])
        self.assertEqual(InvoicePayment.objects.count(), 1)
        provider_factory.return_value.create.assert_called_once()

    @patch("apps.finance.payments.get_pix_service")
    def test_public_page_needs_no_auth_and_exposes_only_allowed_fields(self, provider_factory):
        provider_factory.return_value.create.return_value = self.pix_result()
        invoice = self.create_invoice()
        payment = self.client.post(f"/api/invoices/{invoice.data['id']}/generate-payment/", {}, format="json", **self.headers)
        token = payment.data["public_url"].rsplit("/", 1)[-1]
        self.client.force_authenticate(None)
        response = self.client.get(f"/api/public/payments/{token}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pix_code"], "000201PIXTEST")
        self.assertEqual(response.data["qr_code"], "data:image/png;base64,dGVzdA==")
        self.assertEqual(set(response.data), {"client", "description", "amount", "due_date", "status", "pix_code", "qr_code", "expires_at"})
        self.assertEqual(self.client.patch(f"/api/public/payments/{token}/", {"amount": "1"}, format="json").status_code, 405)
        self.assertEqual(self.client.get("/api/public/payments/00000000-0000-0000-0000-000000000000/").status_code, 404)

    @patch("apps.finance.payments.get_pix_service")
    def test_provider_failure_is_controlled(self, provider_factory):
        provider_factory.return_value.create.side_effect = PaymentProviderError("indisponível")
        invoice = self.create_invoice()
        response = self.client.post(f"/api/invoices/{invoice.data['id']}/generate-payment/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(InvoicePayment.objects.count(), 0)

    @patch("apps.finance.payments.get_pix_service")
    def test_paid_webhook_is_idempotent_and_creates_one_revenue(self, provider_factory):
        provider_factory.return_value.create.return_value = self.pix_result()
        invoice_response = self.create_invoice()
        self.client.post(f"/api/invoices/{invoice_response.data['id']}/generate-payment/", {}, format="json", **self.headers)
        payment = {"id": "mp_test_123", "status": "approved", "transaction_amount": "1500.00", "currency_id": "BRL", "external_reference": f"invoice:{invoice_response.data['id']}"}
        self.assertEqual(process_mercado_pago_payment(payment, "evt_paid"), "paid")
        self.assertEqual(process_mercado_pago_payment(payment, "evt_paid"), "duplicate")
        self.assertEqual(Revenue.objects.filter(invoice_id=invoice_response.data["id"]).count(), 1)
        self.assertEqual(Invoice.objects.get(pk=invoice_response.data["id"]).status, Invoice.Status.PAID)

    @patch("apps.finance.payments.get_pix_service")
    def test_webhook_rejects_wrong_amount_and_preserves_pending(self, provider_factory):
        provider_factory.return_value.create.return_value = self.pix_result()
        invoice_response = self.create_invoice()
        self.client.post(f"/api/invoices/{invoice_response.data['id']}/generate-payment/", {}, format="json", **self.headers)
        payment = {"id": "mp_test_123", "status": "approved", "transaction_amount": "0.01", "currency_id": "BRL", "external_reference": f"invoice:{invoice_response.data['id']}"}
        with self.assertRaises(PaymentProviderError): process_mercado_pago_payment(payment, "evt_wrong")
        self.assertEqual(InvoicePayment.objects.get().status, InvoicePayment.Status.PENDING)
        self.assertFalse(Revenue.objects.exists())

    @patch("apps.subscriptions.views.MercadoPagoClient")
    def test_webhook_validates_provider_signature(self, client_class):
        client_class.verify_webhook.return_value = False
        invalid = self.client.post(
            "/api/webhooks/mercado-pago/?data.id=mp_missing&type=payment",
            data={"type": "payment", "data": {"id": "mp_missing"}},
            format="json",
            HTTP_X_SIGNATURE="invalid",
            HTTP_X_REQUEST_ID="request-id",
        )
        self.assertEqual(invalid.status_code, 400)
        client_class.verify_webhook.return_value = True
        client_class.return_value.get_payment.return_value = {
            "id": "mp_missing",
            "status": "rejected",
            "external_reference": "invoice:999",
        }
        valid = self.client.post(
            "/api/webhooks/mercado-pago/?data.id=mp_missing&type=payment",
            data={"type": "payment", "data": {"id": "mp_missing"}},
            format="json",
            HTTP_X_SIGNATURE="valid",
            HTTP_X_REQUEST_ID="request-id",
        )
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.data["result"], "ignored")
