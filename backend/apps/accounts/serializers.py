from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.FileField(required=False, allow_null=True)
    pending_workspace_approval = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "language",
            "timezone",
            "theme",
            "pending_workspace_approval",
            "date_joined",
            "created_at",
            "updated_at",
            "pending_workspace_approval",
        )
        read_only_fields = (
            "id",
            "username",
            "date_joined",
            "created_at",
            "updated_at",
        )

    def get_pending_workspace_approval(self, obj):
        return obj.memberships.filter(approval_status="PENDING").exists()

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(email=value).exists():
            raise serializers.ValidationError("Já existe uma conta com este email.")
        return value

    def validate_avatar(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("A imagem deve ter no máximo 10 MB.")
        if value and getattr(value, "content_type", "") not in {
            "image/jpeg", "image/png", "image/webp"
        }:
            raise serializers.ValidationError("Use uma imagem JPG, PNG ou WEBP.")
        if value:
            header = value.read(12)
            value.seek(0)
            valid = (
                header.startswith(b"\x89PNG\r\n\x1a\n")
                or header.startswith(b"\xff\xd8\xff")
                or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
            )
            if not valid:
                raise serializers.ValidationError("O conteúdo da imagem é inválido.")
        return value

    def validate_language(self, value):
        if value not in {"pt-BR", "en"}:
            raise serializers.ValidationError("Idioma não suportado.")
        return value

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Fuso horário inválido.") from exc
        return value

    def validate_theme(self, value):
        if value not in {"system", "light", "dark"}:
            raise serializers.ValidationError("Tema inválido.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        old_email = instance.email
        user = super().update(instance, validated_data)
        if user.email.lower() != old_email.lower():
            self._require_email_reapproval(user)
        return user

    def _require_email_reapproval(self, user):
        from apps.organizations.models import OrganizationMembership
        from apps.portal.services import NotificationService

        memberships = OrganizationMembership.objects.filter(
            user=user, is_active=True
        ).exclude(role=OrganizationMembership.Role.OWNER)
        for membership in memberships.select_related("organization__owner"):
            membership.is_active = False
            membership.approval_status = OrganizationMembership.ApprovalStatus.PENDING
            membership.save(update_fields=["is_active", "approval_status"])
            NotificationService.notify(
                organization=membership.organization,
                user=membership.organization.owner,
                type="EMAIL_REAPPROVAL",
                title="Alteração de email aguardando aprovação",
                message=f"{user.get_full_name() or user.email} alterou o email e precisa de nova aprovação.",
                data={"membership_id": membership.id},
            )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password", "password_confirm")
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "As senhas não coincidem."}
            )
        return attrs

    def create(self, data):
        return User.objects.create_user(**data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if not user or not user.is_active:
            raise serializers.ValidationError("Credenciais inválidas.")
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user, context=self.context).data,
        }
