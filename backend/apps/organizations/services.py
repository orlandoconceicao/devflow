from django.db import transaction
from django.utils.text import slugify

from .models import Organization, OrganizationMembership


@transaction.atomic
def create_organization(*, user, name):
    base = slugify(name) or "workspace"
    slug = base
    index = 2
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base}-{index}"
        index += 1
    org = Organization.objects.create(name=name, slug=slug, owner=user)
    OrganizationMembership.objects.create(
        organization=org, user=user, role=OrganizationMembership.Role.OWNER
    )
    from apps.subscriptions.services import create_free_subscription

    create_free_subscription(org)
    return org
