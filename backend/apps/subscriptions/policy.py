from django.db.models import Sum

from apps.work.models import Project, TaskAttachment

PLAN_LIMITS = {
    "free": {
        "active_projects": 3,
        "members": 2,
        "storage_mb": 500,
        "portal": False,
        "exports": False,
        "realtime": False,
    },
    "pro": {
        "active_projects": None,
        "members": 20,
        "storage_mb": 10240,
        "portal": True,
        "exports": True,
        "realtime": True,
    },
}


class SubscriptionPolicy:
    def __init__(self, organization):
        self.organization = organization
        self.subscription = organization.subscription

    @property
    def effective_slug(self):
        return (
            "pro"
            if self.subscription.plan.slug == "pro"
            and self.subscription.status == "ACTIVE"
            else "free"
        )

    @property
    def limits(self):
        return PLAN_LIMITS[self.effective_slug]

    def usage(self):
        storage = (
            TaskAttachment.objects.filter(
                task__organization=self.organization
            ).aggregate(v=Sum("file_size"))["v"]
            or 0
        )
        return {
            "projects": {
                "used": Project.objects.filter(
                    organization=self.organization, status="ACTIVE"
                ).count(),
                "limit": self.limits["active_projects"],
            },
            "members": {
                "used": self.organization.memberships.count(),
                "limit": self.limits["members"],
            },
            "storage": {
                "used": round(storage / 1024 / 1024, 2),
                "limit": self.limits["storage_mb"],
            },
        }

    def can_create_project(self):
        u = self.usage()["projects"]
        return u["limit"] is None or u["used"] < u["limit"]

    def can_invite_member(self):
        u = self.usage()["members"]
        return u["used"] < u["limit"]

    def can_upload_file(self, size):
        u = self.usage()["storage"]
        return u["used"] + size / 1024 / 1024 <= u["limit"]

    def can_use_client_portal(self):
        return self.limits["portal"]

    def can_export_reports(self):
        return self.limits["exports"]
