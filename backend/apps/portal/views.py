import hashlib
import secrets
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.work.context import current_membership
from apps.work.models import Client, Project
from apps.work.serializers import ProjectSerializer

from .models import (
    ClientAccess,
    ClientInvitation,
    DeliverableComment,
    Notification,
    NotificationPreference,
    ProjectDeliverable,
)
from .serializers import (
    DeliverableAttachmentSerializer,
    DeliverableCommentSerializer,
    DeliverableSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)
from .services import NotificationService
from .tasks import send_client_invitation_email


def is_manager(request):
    return current_membership(request).role in (
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
    )


def client_projects(request):
    return Project.objects.filter(
        organization=current_membership(request).organization,
        client__portal_accesses__user=request.user,
    ).distinct()


class DeliverablePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ("create", "update", "partial_update", "destroy"):
            return is_manager(request)
        return True


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(
            user=self.request.user,
            organization=current_membership(self.request).organization,
        )
        return (
            qs.filter(read_at__isnull=True)
            if self.request.query_params.get("read_at__isnull") == "true"
            else qs
        )

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response(
            {"count": self.get_queryset().filter(read_at__isnull=True).count()}
        )

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        item = self.get_object()
        item.read_at = timezone.now()
        item.save(update_fields=["read_at"])
        return Response(self.get_serializer(item).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response(status=204)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        return NotificationPreference.objects.get_or_create(user=self.request.user)[0]


class DeliverableViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverableSerializer
    permission_classes = [permissions.IsAuthenticated, DeliverablePermission]

    def get_queryset(self):
        m = current_membership(self.request)
        qs = (
            ProjectDeliverable.objects.filter(organization=m.organization)
            .select_related("project")
            .prefetch_related("comments__author", "attachments")
        )
        qs = (
            qs.filter(project__in=client_projects(self.request))
            if m.role == OrganizationMembership.Role.CLIENT
            else qs
        )
        return (
            qs.filter(project_id=self.request.query_params["project"])
            if self.request.query_params.get("project")
            else qs
        )

    def perform_create(self, s):
        if not is_manager(self.request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied()
        project = s.validated_data["project"]
        if project.organization_id != current_membership(self.request).organization_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Projeto inválido.")
        s.save(organization=project.organization, created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        d = self.get_object()
        if current_membership(request).role != OrganizationMembership.Role.CLIENT:
            return Response(status=403)
        d.status = ProjectDeliverable.Status.APPROVED
        d.save(update_fields=["status", "updated_at"])
        NotificationService.notify(
            organization=d.organization,
            user=d.created_by,
            type="DELIVERABLE_APPROVED",
            title="Entrega aprovada",
            message=f"{d.title} foi aprovada pelo cliente.",
        )
        return Response(self.get_serializer(d).data)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        d = self.get_object()
        message = str(request.data.get("message", "")).strip()
        if current_membership(request).role != OrganizationMembership.Role.CLIENT:
            return Response(status=403)
        if not message:
            return Response({"message": "Comentário obrigatório."}, status=400)
        DeliverableComment.objects.create(
            deliverable=d, author=request.user, message=message
        )
        d.status = ProjectDeliverable.Status.CHANGES_REQUESTED
        d.save(update_fields=["status", "updated_at"])
        NotificationService.notify(
            organization=d.organization,
            user=d.created_by,
            type="CHANGES_REQUESTED",
            title="Alterações solicitadas",
            message=message,
        )
        return Response(self.get_serializer(d).data)

    @action(detail=True, methods=["post"])
    def comments(self, request, pk=None):
        d = self.get_object()
        s = DeliverableCommentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        row = s.save(deliverable=d, author=request.user)
        return Response(DeliverableCommentSerializer(row).data, status=201)

    @action(detail=True, methods=["post"])
    def attachments(self, request, pk=None):
        d = self.get_object()
        s = DeliverableAttachmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        f = s.validated_data["file"]
        if f.size > 10 * 1024 * 1024:
            return Response({"file": "Limite de 10 MB."}, status=400)
        row = s.save(
            deliverable=d,
            uploaded_by=request.user,
            original_name=Path(f.name).name,
            file_size=f.size,
            content_type=getattr(f, "content_type", "application/octet-stream"),
        )
        return Response(DeliverableAttachmentSerializer(row).data, status=201)


@api_view(["POST"])
def invite_client(request, pk):
    if not is_manager(request):
        return Response(status=403)
    from apps.subscriptions.policy import SubscriptionPolicy

    if not SubscriptionPolicy(
        current_membership(request).organization
    ).can_use_client_portal():
        return Response(
            {"detail": "O portal do cliente está disponível no plano Pro."}, status=403
        )
    client = Client.objects.filter(
        pk=pk, organization=current_membership(request).organization
    ).first()
    if not client:
        return Response(status=404)
    email = str(request.data.get("email", "")).lower().strip()
    if not email:
        return Response({"email": "Obrigatório."}, status=400)
    token = secrets.token_urlsafe(32)
    inv = ClientInvitation.objects.create(
        organization=client.organization,
        client=client,
        email=email,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=timezone.now() + timezone.timedelta(days=7),
        invited_by=request.user,
    )
    send_client_invitation_email.delay(email, token)
    return Response({"id": inv.id, "expires_at": inv.expires_at}, status=201)


@api_view(["POST"])
@transaction.atomic
def accept_invitation(request):
    token = str(request.data.get("token", ""))
    h = hashlib.sha256(token.encode()).hexdigest()
    inv = (
        ClientInvitation.objects.select_for_update()
        .filter(token_hash=h, accepted_at__isnull=True, expires_at__gt=timezone.now())
        .first()
    )
    if not inv or request.user.email.lower() != inv.email.lower():
        return Response({"detail": "Convite inválido ou expirado."}, status=400)
    ClientAccess.objects.get_or_create(
        organization=inv.organization, client=inv.client, user=request.user
    )
    OrganizationMembership.objects.update_or_create(
        organization=inv.organization,
        user=request.user,
        defaults={"role": OrganizationMembership.Role.CLIENT},
    )
    inv.accepted_at = timezone.now()
    inv.save(update_fields=["accepted_at"])
    return Response({"accepted": True})


@api_view(["GET"])
def portal_dashboard(request):
    if current_membership(request).role != OrganizationMembership.Role.CLIENT:
        return Response(status=403)
    qs = client_projects(request)
    return Response(
        {
            "active_projects": qs.filter(status="ACTIVE").count(),
            "pending_deliverables": ProjectDeliverable.objects.filter(
                project__in=qs, status="READY_FOR_REVIEW"
            ).count(),
            "projects": ProjectSerializer(
                qs.select_related("client"), many=True, context={"request": request}
            ).data,
        }
    )


@api_view(["GET"])
def portal_projects(request):
    if current_membership(request).role != OrganizationMembership.Role.CLIENT:
        return Response(status=403)
    return Response(
        ProjectSerializer(
            client_projects(request).select_related("client"),
            many=True,
            context={"request": request},
        ).data
    )
