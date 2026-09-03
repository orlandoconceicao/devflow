from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import OrganizationMembership
from apps.organizations.services import create_organization


class ProfileSecurityTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(email="owner-profile@test.local", password="StrongPass!2026")
        self.member = User.objects.create_user(email="member-profile@test.local", password="StrongPass!2026")
        self.organization = create_organization(user=self.owner, name="Profile Org")
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMembership.Role.MEMBER,
        )

    def test_profile_preferences_avatar_and_email_reapproval(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(
            "/api/auth/me/",
            {
                "first_name": "Maria", "last_name": "Silva", "bio": "Desenvolvedora",
                "email": "maria.silva@test.local", "language": "en",
                "timezone": "America/Sao_Paulo", "theme": "dark",
                "avatar": SimpleUploadedFile("avatar.png", b"\x89PNG\r\n\x1a\nvalid", content_type="image/png"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.membership.refresh_from_db()
        self.assertEqual(self.member.pk, response.data["id"])
        self.assertEqual(self.member.bio, "Desenvolvedora")
        self.assertFalse(self.membership.is_active)
        self.assertEqual(self.membership.approval_status, "PENDING")

        self.client.force_authenticate(self.owner)
        approved = self.client.post(
            f"/api/organizations/{self.organization.id}/members/{self.membership.id}/"
        )
        self.assertEqual(approved.status_code, 200)
        self.membership.refresh_from_db()
        self.assertTrue(self.membership.is_active)
        self.assertEqual(self.membership.approval_status, "APPROVED")

    def test_avatar_rejects_unsupported_content(self):
        self.client.force_authenticate(self.member)
        response = self.client.patch(
            "/api/auth/me/",
            {"avatar": SimpleUploadedFile("avatar.svg", b"<svg/>", content_type="image/svg+xml")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_avatar_accepts_exactly_10_mb_and_rejects_one_byte_more(self):
        self.client.force_authenticate(self.owner)
        header = b"\x89PNG\r\n\x1a\n"
        accepted = SimpleUploadedFile(
            "limit.png",
            header + b"0" * (10 * 1024 * 1024 - len(header)),
            content_type="image/png",
        )
        response = self.client.patch(
            "/api/auth/me/", {"avatar": accepted}, format="multipart"
        )
        self.assertEqual(response.status_code, 200, response.data)

        rejected = SimpleUploadedFile(
            "too-large.png",
            header + b"0" * (10 * 1024 * 1024 + 1 - len(header)),
            content_type="image/png",
        )
        response = self.client.patch(
            "/api/auth/me/", {"avatar": rejected}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("10 MB", str(response.data))

    def test_avatar_rejects_spoofed_image_content(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            "/api/auth/me/",
            {
                "avatar": SimpleUploadedFile(
                    "fake.png", b"not-an-image", content_type="image/png"
                )
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("conteúdo", str(response.data).lower())


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="logout@test.local", password="StrongPass!2026"
        )

    def test_logout_blacklists_refresh_and_protected_route_requires_auth(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            "/api/auth/logout/", {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, 204)

        self.client.credentials()
        self.assertEqual(self.client.get("/api/projects/").status_code, 401)
        refreshed = self.client.post(
            "/api/auth/refresh/", {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(refreshed.status_code, 401)

    def test_invalid_refresh_returns_clear_client_error(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/auth/logout/", {"refresh": "invalid"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "invalid_token")
