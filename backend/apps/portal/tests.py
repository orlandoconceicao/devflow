import hashlib
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership
from apps.portal.models import (
    ClientAccess,
    ClientInvitation,
    Notification,
    ProjectDeliverable,
)


class PortalBillingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)

    def login(self, user):
        r = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "StrongPass!2026"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def setup_org(self):
        owner = User.objects.create_user(
            email="owner5@test.local", password="StrongPass!2026"
        )
        self.login(owner)
        org = self.client.post(
            "/api/organizations/", {"name": "Portal Org"}, format="json"
        ).data
        h = {"HTTP_X_ORGANIZATION_ID": str(org["id"])}
        client = self.client.post(
            "/api/clients/", {"name": "Cliente"}, format="json", **h
        ).data
        project = self.client.post(
            "/api/projects/",
            {"name": "Portal project", "client": client["id"], "status": "ACTIVE"},
            format="json",
            **h,
        ).data
        return owner, org, h, client, project

    def test_free_limit_and_price_owned_by_backend(self):
        owner, org, h, client, project = self.setup_org()
        for i in range(2):
            self.assertEqual(
                self.client.post(
                    "/api/projects/",
                    {"name": f"P{i}", "client": client["id"], "status": "ACTIVE"},
                    format="json",
                    **h,
                ).status_code,
                201,
            )
        self.assertEqual(
            self.client.post(
                "/api/projects/",
                {"name": "Fourth", "client": client["id"], "status": "ACTIVE"},
                format="json",
                **h,
            ).status_code,
            403,
        )
        usage = self.client.get("/api/billing/usage/", **h)
        self.assertEqual(usage.data["projects"], {"used": 3, "limit": 3})
        self.assertEqual(
            str(org and owner.owned_organizations.first().subscription.plan.price),
            "0.00",
        )

    def test_invitation_portal_isolation_and_approval(self):
        owner, org, h, client, project = self.setup_org()
        guest = User.objects.create_user(
            email="guest5@test.local", password="StrongPass!2026"
        )
        token = "safe-token"
        inv = ClientInvitation.objects.create(
            organization_id=org["id"],
            client_id=client["id"],
            email=guest.email,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(days=1),
            invited_by=owner,
        )
        self.login(guest)
        self.assertEqual(
            self.client.post(
                "/api/client-invitations/accept/", {"token": token}, format="json", **h
            ).status_code,
            200,
        )
        self.assertTrue(
            ClientAccess.objects.filter(user=guest, client_id=client["id"]).exists()
        )
        d = ProjectDeliverable.objects.create(
            organization_id=org["id"],
            project_id=project["id"],
            title="Entrega",
            status="READY_FOR_REVIEW",
            created_by=owner,
        )
        self.assertEqual(
            self.client.post(
                f"/api/deliverables/{d.id}/approve/", {}, format="json", **h
            ).status_code,
            200,
        )
        d.refresh_from_db()
        self.assertEqual(d.status, "APPROVED")
        self.assertEqual(
            self.client.get("/api/finance/dashboard/", **h).status_code, 403
        )

    def test_notifications_are_private_and_readable(self):
        owner, org, h, client, project = self.setup_org()
        other = User.objects.create_user(
            email="other5@test.local", password="StrongPass!2026"
        )
        OrganizationMembership.objects.create(
            organization_id=org["id"], user=other, role="MEMBER"
        )
        n = Notification.objects.create(
            organization_id=org["id"],
            user=owner,
            type="PROJECT_UPDATE",
            title="Atualização",
            message="Projeto atualizado",
        )
        self.assertEqual(
            self.client.get("/api/notifications/unread-count/", **h).data["count"], 1
        )
        self.assertEqual(
            self.client.post(
                f"/api/notifications/{n.id}/read/", {}, format="json", **h
            ).status_code,
            200,
        )
        self.login(other)
        self.assertEqual(
            self.client.get(f"/api/notifications/{n.id}/", **h).status_code, 404
        )
