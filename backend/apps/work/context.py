from rest_framework.exceptions import PermissionDenied
from apps.organizations.models import OrganizationMembership
def current_membership(request):
    qs=OrganizationMembership.objects.select_related("organization").filter(user=request.user)
    organization_id=request.headers.get("X-Organization-ID")
    if organization_id: qs=qs.filter(organization_id=organization_id)
    membership=qs.order_by("joined_at").first()
    if not membership: raise PermissionDenied("Você não possui acesso a este workspace.")
    return membership

