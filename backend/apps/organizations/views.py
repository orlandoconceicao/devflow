from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.work.context import current_membership
from apps.work.services import log_activity

from .models import Organization, OrganizationMembership, TeamInvitation
from .permissions import IsOrganizationMember, IsOrganizationOwner
from .serializers import (
    MembershipSerializer,
    OrganizationSerializer,
    TeamInvitationAcceptSerializer,
    TeamInvitationCreateSerializer,
    TeamInvitationPublicSerializer,
    TeamMessageSerializer,
)
from .tasks import send_team_invitation_email


def owner_organization(request, pk):
    org = Organization.objects.filter(pk=pk, owner=request.user).first()
    if not org:
        raise NotFound()
    return org


class OrganizationListCreateView(generics.ListCreateAPIView):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return (
            Organization.objects.filter(memberships__user=self.request.user, memberships__is_active=True)
            .distinct()
            .select_related("owner")
            .order_by("created_at")
        )


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user, memberships__is_active=True
        ).distinct()

    def get_permissions(self):
        return (
            [permissions.IsAuthenticated(), IsOrganizationOwner()]
            if self.request.method in ("PATCH", "PUT")
            else super().get_permissions()
        )


class OrganizationMembersView(generics.ListAPIView):
    serializer_class = MembershipSerializer

    def get_queryset(self):
        try:
            org = Organization.objects.get(pk=self.kwargs["pk"], owner=self.request.user)
        except Organization.DoesNotExist:
            raise NotFound()
        return org.memberships.filter(role__in=["OWNER", "ADMIN", "MEMBER"]).select_related("user")


class TeamInvitationCreateView(APIView):
    def get(self, request, pk):
        org = owner_organization(request, pk)
        invitations = org.team_invitations.filter(
            status=TeamInvitation.Status.PENDING, expires_at__gt=timezone.now()
        ).select_related("organization").order_by("-created_at")
        return Response(TeamInvitationPublicSerializer(invitations, many=True).data)

    def post(self, request, pk):
        org = owner_organization(request, pk)
        serializer = TeamInvitationCreateSerializer(data=request.data, context={"organization": org})
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        TeamInvitation.objects.filter(
            organization=org, email=email, status=TeamInvitation.Status.PENDING
        ).update(status=TeamInvitation.Status.CANCELLED)
        invitation, token = TeamInvitation.issue(
            organization=org, email=email, role=serializer.validated_data["role"], invited_by=request.user
        )
        send_team_invitation_email.delay(email, org.name, token)
        log_activity(organization=org, user=request.user, action="TEAM_MEMBER_INVITED", entity=invitation)
        return Response(
            {**TeamInvitationPublicSerializer(invitation).data,
             "invite_url": f"{__import__('django.conf', fromlist=['settings']).settings.FRONTEND_URL}/team-invitations/accept?token={token}"},
            status=status.HTTP_201_CREATED,
        )


class TeamInvitationDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        invitation = TeamInvitation.objects.select_related("organization").filter(
            token_hash=TeamInvitation.hash_token(token), status=TeamInvitation.Status.PENDING
        ).first()
        if not invitation or invitation.is_expired:
            raise NotFound()
        return Response(TeamInvitationPublicSerializer(invitation).data)


class TeamInvitationAcceptView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TeamInvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        log_activity(
            organization=invitation.organization, user=None,
            action="TEAM_INVITATION_ACCEPTED", entity=invitation,
        )
        return Response({"detail": "Convite aceito. Entre normalmente em /login."})


class OrganizationMemberDetailView(APIView):
    def post(self, request, pk, membership_id):
        org = owner_organization(request, pk)
        membership = org.memberships.filter(
            pk=membership_id,
            approval_status=OrganizationMembership.ApprovalStatus.PENDING,
        ).first()
        if not membership:
            raise NotFound()
        membership.is_active = True
        membership.approval_status = OrganizationMembership.ApprovalStatus.APPROVED
        membership.save(update_fields=["is_active", "approval_status"])
        return Response(MembershipSerializer(membership).data)

    def patch(self, request, pk, membership_id):
        org = owner_organization(request, pk)
        membership = org.memberships.select_related("user").filter(pk=membership_id).first()
        if not membership:
            raise NotFound()
        if membership.role == OrganizationMembership.Role.OWNER:
            raise PermissionDenied("O Owner não pode ter sua função alterada.")
        role = request.data.get("role")
        if role not in (OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.MEMBER):
            return Response({"role": "Função inválida."}, status=400)
        membership.role = role
        membership.save(update_fields=["role"])
        log_activity(organization=org, user=request.user, action="TEAM_MEMBER_ROLE_CHANGED", entity=membership, metadata={"role": role})
        return Response(MembershipSerializer(membership).data)

    def delete(self, request, pk, membership_id):
        org = owner_organization(request, pk)
        membership = org.memberships.filter(pk=membership_id).first()
        if not membership:
            raise NotFound()
        if membership.role == OrganizationMembership.Role.OWNER or membership.user_id == request.user.id:
            raise PermissionDenied("O Owner não pode ser removido.")
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        membership.user.project_memberships.filter(project__organization=org).delete()
        log_activity(organization=org, user=request.user, action="TEAM_MEMBER_REMOVED", entity=membership)
        return Response(status=204)


class TeamMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = TeamMessageSerializer
    pagination_class = None

    def get_queryset(self):
        membership = current_membership(self.request)
        return membership.organization.team_messages.select_related("author")

    def perform_create(self, serializer):
        membership = current_membership(self.request)
        serializer.save(organization=membership.organization, author=self.request.user)
