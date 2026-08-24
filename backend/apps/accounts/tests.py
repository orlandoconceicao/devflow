from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

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
