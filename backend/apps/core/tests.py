from decimal import Decimal

from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership
from apps.subscriptions.models import Subscription


class DevFlowAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)

    def register(self, email="ana@example.com", password="StrongPass!2026"):
        return self.client.post(
            "/api/auth/register/",
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "email": email,
                "password": password,
                "password_confirm": password,
            },
            format="json",
        )

    def auth(self, email="ana@example.com", password="StrongPass!2026"):
        response = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}, format="json"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response

    def test_registration_login_profile_and_logout(self):
        self.assertEqual(self.register().status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", self.register("bia@example.com").data)
        self.assertEqual(self.register().status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.register("weak@example.com", "123").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        login = self.auth()
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        refreshed = self.client.post(
            "/api/auth/refresh/", {"refresh": login.data["refresh"]}, format="json"
        )
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)
        self.assertEqual(
            self.client.get("/api/auth/me/").status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            self.client.patch(
                "/api/auth/me/",
                {"first_name": "Anita", "is_staff": True},
                format="json",
            ).data["first_name"],
            "Anita",
        )
        self.assertFalse(User.objects.get(email="ana@example.com").is_staff)
        self.assertEqual(
            self.client.post(
                "/api/auth/logout/",
                {"refresh": refreshed.data.get("refresh", login.data["refresh"])},
            ).status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.client.credentials()
        self.assertEqual(
            self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(
            self.client.post(
                "/api/auth/login/", {"email": "ana@example.com", "password": "bad"}
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post("/api/auth/refresh/", {"refresh": "bad"}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_workspace_owner_free_subscription_and_plans(self):
        self.register()
        self.auth()
        response = self.client.post(
            "/api/organizations/", {"name": "Aurora Studio"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org_id = response.data["id"]
        self.assertTrue(
            OrganizationMembership.objects.filter(
                organization_id=org_id, role="OWNER"
            ).exists()
        )
        subscription = Subscription.objects.get(organization_id=org_id)
        self.assertEqual(subscription.plan.slug, "free")
        self.assertEqual(subscription.status, "ACTIVE")
        plans = self.client.get("/api/plans/").data
        pro = next(p for p in plans if p["slug"] == "pro")
        self.assertEqual(Decimal(pro["price"]), Decimal("25.00"))
        self.assertEqual(pro["billing_interval"], "MONTHLY")
        self.assertEqual(
            self.client.patch(
                "/api/subscription/", {"plan": "pro"}, format="json"
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_health_request_id_and_password_reset(self):
        health = self.client.get("/health/")
        self.assertEqual(health.status_code, 200)
        self.assertIn("X-Request-ID", health.headers)
        self.register("reset@example.com")
        unknown = self.client.post(
            "/api/auth/password-reset/", {"email": "unknown@example.com"}, format="json"
        )
        known = self.client.post(
            "/api/auth/password-reset/", {"email": "reset@example.com"}, format="json"
        )
        self.assertEqual(unknown.data, known.data)
        user = User.objects.get(email="reset@example.com")
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
            "password": "AnotherStrong!2026",
        }
        self.assertEqual(
            self.client.post(
                "/api/auth/password-reset/confirm/", payload, format="json"
            ).status_code,
            200,
        )
        self.assertTrue(
            user.__class__.objects.get(pk=user.pk).check_password("AnotherStrong!2026")
        )

    def test_multitenant_isolation_and_rbac(self):
        self.register()
        self.auth()
        org_a = self.client.post(
            "/api/organizations/", {"name": "A"}, format="json"
        ).data
        self.client.credentials()
        self.register("bob@example.com")
        self.auth("bob@example.com")
        org_b = self.client.post(
            "/api/organizations/", {"name": "B"}, format="json"
        ).data
        self.assertEqual(
            self.client.get(f"/api/organizations/{org_a['id']}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(f"/api/organizations/{org_a['id']}/members/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(
                f"/api/subscription/?organization_id={org_a['id']}"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        bob = User.objects.get(email="bob@example.com")
        self.client.credentials()
        self.register("carol@example.com")
        self.auth("carol@example.com")
        org_c = self.client.post(
            "/api/organizations/", {"name": "C"}, format="json"
        ).data
        OrganizationMembership.objects.create(
            organization_id=org_c["id"], user=bob, role="ADMIN"
        )
        self.client.credentials()
        self.auth("bob@example.com")
        self.assertEqual(
            self.client.patch(
                f"/api/organizations/{org_c['id']}/", {"name": "Hacked"}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
