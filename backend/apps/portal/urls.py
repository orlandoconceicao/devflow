from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DeliverableViewSet,
    NotificationPreferenceView,
    NotificationViewSet,
    accept_invitation,
    invite_client,
    portal_dashboard,
    portal_projects,
)

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("deliverables", DeliverableViewSet, basename="deliverable")
urlpatterns = [
    path("", include(router.urls)),
    path("notification-preferences/", NotificationPreferenceView.as_view()),
    path("clients/<int:pk>/invite/", invite_client),
    path("client-invitations/accept/", accept_invitation),
    path("client-portal/dashboard/", portal_dashboard),
    path("client-portal/projects/", portal_projects),
]
