from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.models import OrganizationMembership

from .context import current_membership


class ClientAccessPermission(BasePermission):
    def has_permission(self, request, view):
        role = current_membership(request).role
        if role == OrganizationMembership.Role.CLIENT:
            return False
        return request.method in SAFE_METHODS or role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        )


class ProjectAccessPermission(BasePermission):
    def has_permission(self, request, view):
        role = current_membership(request).role
        if role == OrganizationMembership.Role.CLIENT:
            return False
        return request.method in SAFE_METHODS or role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        )


class ManageProjectMembersPermission(BasePermission):
    def has_permission(self, request, view):
        return current_membership(request).role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        )


class TaskAccessPermission(BasePermission):
    def has_permission(self, request, view):
        return current_membership(request).role != OrganizationMembership.Role.CLIENT
