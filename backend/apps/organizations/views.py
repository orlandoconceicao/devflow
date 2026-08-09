from rest_framework import generics,permissions
from rest_framework.exceptions import NotFound
from .models import Organization
from .permissions import IsOrganizationMember,IsOrganizationOwner
from .serializers import MembershipSerializer,OrganizationSerializer
class OrganizationListCreateView(generics.ListCreateAPIView):
    serializer_class=OrganizationSerializer
    def get_queryset(self): return Organization.objects.filter(memberships__user=self.request.user).distinct().select_related("owner")
class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class=OrganizationSerializer; permission_classes=[permissions.IsAuthenticated,IsOrganizationMember]
    def get_queryset(self): return Organization.objects.filter(memberships__user=self.request.user).distinct()
    def get_permissions(self): return [permissions.IsAuthenticated(),IsOrganizationOwner()] if self.request.method in ("PATCH","PUT") else super().get_permissions()
class OrganizationMembersView(generics.ListAPIView):
    serializer_class=MembershipSerializer
    def get_queryset(self):
        try: org=Organization.objects.filter(memberships__user=self.request.user).get(pk=self.kwargs["pk"])
        except Organization.DoesNotExist: raise NotFound()
        return org.memberships.select_related("user")

