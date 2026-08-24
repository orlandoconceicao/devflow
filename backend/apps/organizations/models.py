import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"
        CLIENT = "CLIENT", "Client"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "user"), name="unique_org_member"
            )
        ]


class TeamInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Convite pendente"
        ACCEPTED = "ACCEPTED", "Aceito"
        CANCELLED = "CANCELLED", "Cancelado"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="team_invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=10,
        choices=[
            (OrganizationMembership.Role.ADMIN, "Admin"),
            (OrganizationMembership.Role.MEMBER, "Member"),
        ],
        default=OrganizationMembership.Role.MEMBER,
    )
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="team_invitations_sent"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=models.Q(status="PENDING"),
                name="one_pending_team_invite_per_email",
            )
        ]

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def issue(cls, **kwargs):
        token = secrets.token_urlsafe(32)
        invitation = cls.objects.create(
            token_hash=cls.hash_token(token),
            expires_at=timezone.now() + timedelta(days=7),
            **kwargs,
        )
        return invitation, token

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()
