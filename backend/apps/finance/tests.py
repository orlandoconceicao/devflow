from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership


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
