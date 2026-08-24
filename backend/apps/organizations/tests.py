from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import OrganizationMembership, TeamInvitation


class TeamApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)

    def setUp(self):
        self.owner = User.objects.create_user(email="owner-team@test.local", password="StrongPass!2026", first_name="Owner")
        self.client.force_authenticate(self.owner)
        self.organization = self.client.post("/api/organizations/", {"name": "Equipe A"}, format="json").data
        self.headers = {"HTTP_X_ORGANIZATION_ID": str(self.organization["id"])}

    @patch("apps.organizations.views.send_team_invitation_email.delay")
    def invite(self, email, send):
        response = self.client.post(
            f"/api/organizations/{self.organization['id']}/team-invitations/",
            {"email": email, "role": "MEMBER"}, format="json", **self.headers,
        )
        self.assertEqual(response.status_code, 201, response.data)
        send.assert_called_once()
        return response.data["invite_url"].split("token=", 1)[1]

    def test_owner_is_created_and_only_owner_manages_team(self):
        owner_membership = OrganizationMembership.objects.get(organization_id=self.organization["id"], user=self.owner)
        self.assertEqual(owner_membership.role, "OWNER")
        self.assertTrue(owner_membership.is_active)
        member = User.objects.create_user(email="plain-member@test.local", password="StrongPass!2026")
        OrganizationMembership.objects.create(organization_id=self.organization["id"], user=member, role="MEMBER")
        self.client.force_authenticate(member)
        self.assertEqual(self.client.get(f"/api/organizations/{self.organization['id']}/members/", **self.headers).status_code, 404)
        self.assertEqual(self.client.post(f"/api/organizations/{self.organization['id']}/team-invitations/", {"email":"x@test.local","role":"MEMBER"}, format="json", **self.headers).status_code, 404)

    def test_invitation_new_user_login_expiration_and_single_use(self):
        token = self.invite("new-member@test.local")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/organizations/team-invitations/{token}/").status_code, 200)
        accepted = self.client.post("/api/organizations/team-invitations/accept/", {
            "token": token, "first_name": "New", "last_name": "Member", "password": "StrongPass!2026"
        }, format="json")
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(self.client.post("/api/organizations/team-invitations/accept/", {"token":token,"password":"StrongPass!2026"}, format="json").status_code, 400)
        login = self.client.post("/api/auth/login/", {"email":"new-member@test.local","password":"StrongPass!2026"}, format="json")
        self.assertEqual(login.status_code, 200)
        invitation = TeamInvitation.objects.get(email="new-member@test.local")
        self.assertEqual(invitation.status, TeamInvitation.Status.ACCEPTED)

        self.client.force_authenticate(self.owner)
        expired_token = self.invite("expired@test.local")
        TeamInvitation.objects.filter(email="expired@test.local").update(expires_at=timezone.now()-timedelta(seconds=1))
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/organizations/team-invitations/{expired_token}/").status_code, 404)

    def test_existing_user_is_not_duplicated_and_needs_own_password(self):
        existing = User.objects.create_user(email="existing@test.local", password="ExistingPass!2026")
        token = self.invite(existing.email)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/organizations/team-invitations/accept/", {"token":token,"password":"wrong"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/organizations/team-invitations/accept/", {"token":token,"password":"ExistingPass!2026"}, format="json").status_code, 200)
        self.assertEqual(User.objects.filter(email=existing.email).count(), 1)

    def test_role_validation_removal_revokes_current_jwt_and_cross_workspace_isolation(self):
        member = User.objects.create_user(email="remove@test.local", password="StrongPass!2026")
        membership = OrganizationMembership.objects.create(organization_id=self.organization["id"], user=member, role="MEMBER")
        self.assertEqual(self.client.patch(f"/api/organizations/{self.organization['id']}/members/{membership.id}/", {"role":"OWNER"}, format="json", **self.headers).status_code, 400)
        self.assertEqual(self.client.patch(f"/api/organizations/{self.organization['id']}/members/{membership.id}/", {"role":"ADMIN"}, format="json", **self.headers).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/organizations/{self.organization['id']}/members/{membership.id}/", **self.headers).status_code, 204)
        self.client.force_authenticate(member)
        self.assertEqual(self.client.get("/api/dashboard/", **self.headers).status_code, 403)
        self.assertFalse(self.client.get("/api/organizations/").data["results"])

        owner_b = User.objects.create_user(email="owner-b@test.local", password="StrongPass!2026")
        self.client.force_authenticate(owner_b)
        organization_b = self.client.post("/api/organizations/", {"name":"Equipe B"}, format="json").data
        self.assertEqual(self.client.get(f"/api/organizations/{self.organization['id']}/members/", HTTP_X_ORGANIZATION_ID=str(organization_b["id"])).status_code, 404)

    def test_owner_cannot_be_removed_or_demoted(self):
        membership = OrganizationMembership.objects.get(organization_id=self.organization["id"], user=self.owner)
        url = f"/api/organizations/{self.organization['id']}/members/{membership.id}/"
        self.assertEqual(self.client.delete(url, **self.headers).status_code, 403)
        self.assertEqual(self.client.patch(url, {"role":"MEMBER"}, format="json", **self.headers).status_code, 403)
