from apps.core.views import health, ready
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("health/", health),
    path("health/ready/", ready),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/organizations/", include("apps.organizations.urls")),
    path("api/", include("apps.subscriptions.urls")),
    path("api/", include("apps.work.urls")),
    path("api/", include("apps.finance.urls")),
    path("api/", include("apps.portal.urls")),
]
