from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClientViewSet,
    ProjectViewSet,
    TaskAttachmentViewSet,
    TaskCommentViewSet,
    TaskLabelViewSet,
    TaskViewSet,
    dashboard,
)

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")
router.register("task-labels", TaskLabelViewSet, basename="task-label")
router.register("task-comments", TaskCommentViewSet, basename="task-comment")
router.register("task-attachments", TaskAttachmentViewSet, basename="task-attachment")
urlpatterns = [path("", include(router.urls)), path("dashboard/", dashboard)]
