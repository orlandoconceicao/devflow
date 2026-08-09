from rest_framework.permissions import BasePermission
from .models import OrganizationMembership
class IsOrganizationMember(BasePermission):
    def has_object_permission(self,request,view,obj): return obj.memberships.filter(user=request.user).exists()
class IsOrganizationOwner(BasePermission):
    def has_object_permission(self,request,view,obj): return obj.owner_id==request.user.id
class IsOrganizationAdminOrOwner(BasePermission):
    def has_object_permission(self,request,view,obj): return obj.memberships.filter(user=request.user,role__in=[OrganizationMembership.Role.OWNER,OrganizationMembership.Role.ADMIN]).exists()

