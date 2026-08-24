from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from .models import Organization, OrganizationMembership, TeamInvitation, TeamMessage
from .services import create_organization


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ("id", "user", "role", "is_active", "approval_status", "joined_at")
        read_only_fields = ("is_active", "approval_status")


class TeamMessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TeamMessage
        fields = ("id", "author", "message", "created_at")
        read_only_fields = ("author", "created_at")

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A mensagem não pode ficar vazia.")
        return value


class TeamInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.MEMBER]
    )

    def validate_email(self, value):
        email = value.strip().lower()
        org = self.context["organization"]
        if org.memberships.filter(user__email=email, is_active=True).exists():
            raise serializers.ValidationError("Este usuário já pertence à equipe.")
        return email


class TeamInvitationPublicSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name")

    class Meta:
        model = TeamInvitation
        fields = ("id", "email", "role", "organization_name", "expires_at", "status")


class TeamInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=False)
    last_name = serializers.CharField(required=False, allow_blank=False)
    password = serializers.CharField(write_only=True)

    @transaction.atomic
    def create(self, data):
        invitation = TeamInvitation.objects.select_for_update().select_related("organization").filter(
            token_hash=TeamInvitation.hash_token(data["token"]), status=TeamInvitation.Status.PENDING
        ).first()
        if not invitation or invitation.is_expired:
            raise serializers.ValidationError({"token": "Convite inválido ou expirado."})
        User = get_user_model()
        user = User.objects.filter(email=invitation.email).first()
        if user:
            user = authenticate(email=invitation.email, password=data["password"])
            if not user:
                raise serializers.ValidationError({"password": "Senha inválida para esta conta."})
        else:
            validate_password(data["password"])
            if not data.get("first_name") or not data.get("last_name"):
                raise serializers.ValidationError("Nome e sobrenome são obrigatórios para uma nova conta.")
            user = User.objects.create_user(
                email=invitation.email, password=data["password"],
                first_name=data["first_name"], last_name=data["last_name"],
            )
        OrganizationMembership.objects.update_or_create(
            organization=invitation.organization,
            user=user,
            defaults={"role": invitation.role, "is_active": True},
        )
        invitation.status = TeamInvitation.Status.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])
        return invitation


class OrganizationSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "owner", "role", "created_at", "updated_at")
        read_only_fields = ("slug", "owner")

    def get_role(self, obj):
        membership = obj.memberships.filter(user=self.context["request"].user).first()
        return membership.role if membership else None

    def create(self, data):
        return create_organization(user=self.context["request"].user, name=data["name"])
