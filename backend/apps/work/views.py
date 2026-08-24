from datetime import date
from pathlib import Path

from django.db import transaction
from django.db.models import Count, Max, Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .context import current_membership
from .models import (
    ActivityLog,
    Client,
    Project,
    ProjectMember,
    Task,
    TaskAttachment,
    TaskComment,
    TaskLabel,
)
from .permissions import (
    ClientAccessPermission,
    ManageProjectMembersPermission,
    ProjectAccessPermission,
    TaskAccessPermission,
)
from .serializers import (
    ActivitySerializer,
    ClientSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
    TaskAttachmentSerializer,
    TaskCommentSerializer,
    TaskLabelSerializer,
    TaskListSerializer,
    TaskSerializer,
)
from .services import log_activity, normalize_positions, recalculate_project_progress


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, ClientAccessPermission]
    filterset_fields = ["status"]
    search_fields = ["name", "company", "email"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_queryset(self):
        return (
            Client.objects.filter(
                organization=current_membership(self.request).organization
            )
            .annotate(project_count=Count("projects"))
            .select_related("created_by")
            .order_by("name")
        )

    def perform_create(self, s):
        m = current_membership(self.request)
        obj = s.save(organization=m.organization, created_by=self.request.user)
        log_activity(
            organization=m.organization,
            user=self.request.user,
            action="CLIENT_CREATED",
            entity=obj,
        )

    def perform_update(self, s):
        obj = s.save()
        log_activity(
            organization=obj.organization,
            user=self.request.user,
            action="CLIENT_UPDATED",
            entity=obj,
        )


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectAccessPermission]
    filterset_fields = [
        "status",
        "priority",
        "client",
        "created_by",
        "start_date",
        "due_date",
    ]
    search_fields = ["name", "description", "client__name", "client__company"]
    ordering_fields = ["created_at", "updated_at", "due_date", "name", "progress"]

    def get_queryset(self):
        m = current_membership(self.request)
        qs = (
            Project.objects.filter(organization=m.organization)
            .select_related("client", "created_by")
            .prefetch_related("members__user")
        )
        return (
            (qs.filter(members__user=self.request.user) if m.role == "MEMBER" else qs)
            .distinct()
            .order_by("-created_at")
        )

    def perform_create(self, s):
        m = current_membership(self.request)
        from apps.subscriptions.policy import SubscriptionPolicy

        if not SubscriptionPolicy(m.organization).can_create_project():
            raise PermissionDenied("Seu plano Free permite até 3 projetos ativos.")
        obj = s.save(organization=m.organization, created_by=self.request.user)
        ProjectMember.objects.get_or_create(
            project=obj, user=self.request.user, defaults={"role": "PROJECT_MANAGER"}
        )
        log_activity(
            organization=m.organization,
            user=self.request.user,
            action="PROJECT_CREATED",
            entity=obj,
        )

    def perform_update(self, s):
        obj = s.save()
        log_activity(
            organization=obj.organization,
            user=self.request.user,
            action="PROJECT_UPDATED",
            entity=obj,
        )

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members_action(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            return Response(
                ProjectMemberSerializer(
                    project.members.select_related("user"), many=True
                ).data
            )
        if not ManageProjectMembersPermission().has_permission(request, self):
            return Response(status=403)
        s = ProjectMemberSerializer(data=request.data, context={"project": project})
        s.is_valid(raise_exception=True)
        member = s.save(project=project)
        log_activity(
            organization=project.organization,
            user=request.user,
            action="PROJECT_MEMBER_ADDED",
            entity=member,
            metadata={"project_id": project.id},
        )
        return Response(ProjectMemberSerializer(member).data, status=201)

    @action(
        detail=True, methods=["delete"], url_path=r"members/(?P<membership_id>[^/.]+)"
    )
    def remove_member(self, request, pk=None, membership_id=None):
        project = self.get_object()
        if not ManageProjectMembersPermission().has_permission(request, self):
            return Response(status=403)
        member = project.members.filter(pk=membership_id).first()
        if not member:
            return Response(status=404)
        member.delete()
        return Response(status=204)

    @action(detail=True, methods=["get"])
    def activities(self, request, pk=None):
        project = self.get_object()
        qs = (
            ActivityLog.objects.filter(organization=project.organization)
            .filter(
                Q(entity_type="Project", entity_id=project.id)
                | Q(metadata__project_id=project.id)
            )
            .select_related("user")[:50]
        )
        return Response(ActivitySerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def tasks(self, request, pk=None):
        project = self.get_object()
        qs = TaskViewSet.base_queryset_for(request).filter(project=project)
        return Response(
            TaskListSerializer(qs, many=True, context={"request": request}).data
        )


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TaskAccessPermission]
    filterset_fields = [
        "project",
        "status",
        "priority",
        "assignees__user",
        "labels",
        "due_date",
    ]
    search_fields = ["title", "description", "project__name"]
    ordering_fields = ["position", "due_date", "priority", "created_at", "updated_at"]

    @staticmethod
    def base_queryset_for(request):
        m = current_membership(request)
        qs = (
            Task.objects.filter(organization=m.organization)
            .select_related("project", "project__client", "created_by")
            .prefetch_related("assignees__user", "labels")
            .annotate(
                comments_count=Count("comments", distinct=True),
                attachments_count=Count("attachments", distinct=True),
            )
        )
        return (
            (
                qs.filter(project__members__user=request.user)
                if m.role == "MEMBER"
                else qs
            )
            .distinct()
            .order_by("status", "position", "id")
        )

    def get_queryset(self):
        return self.base_queryset_for(self.request)

    def get_serializer_class(self):
        return TaskListSerializer if self.action == "list" else TaskSerializer

    def perform_create(self, s):
        project = s.validated_data["project"]
        max_pos = Task.objects.filter(
            project=project, status=s.validated_data.get("status", Task.Status.TODO)
        ).aggregate(v=Max("position"))["v"]
        task = s.save(
            organization=project.organization,
            created_by=self.request.user,
            position=(max_pos + 1 if max_pos is not None else 0),
        )
        recalculate_project_progress(project)
        log_activity(
            organization=project.organization,
            user=self.request.user,
            action="TASK_CREATED",
            entity=task,
            metadata={"project_id": project.id},
        )

    def perform_update(self, s):
        old = s.instance.status
        task = s.save()
        action = "TASK_UPDATED"
        if task.status == Task.Status.DONE and old != Task.Status.DONE:
            task.completed_at = timezone.now()
            task.save(update_fields=["completed_at"])
            action = "TASK_COMPLETED"
        elif old == Task.Status.DONE and task.status != Task.Status.DONE:
            task.completed_at = None
            task.save(update_fields=["completed_at"])
            action = "TASK_REOPENED"
        recalculate_project_progress(task.project)
        log_activity(
            organization=task.organization,
            user=self.request.user,
            action=action,
            entity=task,
            metadata={"project_id": task.project_id},
        )

    def perform_destroy(self, obj):
        project = obj.project
        obj.delete()
        recalculate_project_progress(project)

    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def move(self, request, pk=None):
        task = self.get_object()
        old = task.status
        new = request.data.get("status")
        if new not in Task.Status.values:
            return Response({"detail": "Status inválido."}, status=400)
        try:
            position = max(0, int(request.data.get("position")))
        except (TypeError, ValueError):
            return Response({"detail": "Posição inválida."}, status=400)
        siblings = list(
            Task.objects.select_for_update()
            .filter(project=task.project, status=new)
            .exclude(pk=task.pk)
            .order_by("position", "id")
        )
        siblings.insert(min(position, len(siblings)), task)
        Task.objects.filter(pk=task.pk).update(
            status=new, completed_at=timezone.now() if new == Task.Status.DONE else None
        )
        for index, item in enumerate(siblings):
            Task.objects.filter(pk=item.pk).update(position=index)
        if old != new:
            normalize_positions(project=task.project, status=old)
        recalculate_project_progress(task.project)
        task.refresh_from_db()
        action = (
            "TASK_COMPLETED"
            if new == Task.Status.DONE
            else "TASK_REOPENED" if old == Task.Status.DONE else "TASK_MOVED"
        )
        log_activity(
            organization=task.organization,
            user=request.user,
            action=action,
            entity=task,
            metadata={"from": old, "to": new, "project_id": task.project_id},
        )
        return Response(TaskSerializer(task, context={"request": request}).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            return Response(
                TaskCommentSerializer(
                    task.comments.select_related("author"), many=True
                ).data
            )
        s = TaskCommentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = s.save(task=task, author=request.user)
        log_activity(
            organization=task.organization,
            user=request.user,
            action="COMMENT_CREATED",
            entity=obj,
            metadata={"task_id": task.id, "project_id": task.project_id},
        )
        return Response(TaskCommentSerializer(obj).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def attachments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            return Response(
                TaskAttachmentSerializer(
                    task.attachments.select_related("uploaded_by"),
                    many=True,
                    context={"request": request},
                ).data
            )
        s = TaskAttachmentSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        file = s.validated_data["file"]
        obj = s.save(
            task=task,
            uploaded_by=request.user,
            original_name=Path(file.name).name,
            file_size=file.size,
            content_type=file.content_type,
        )
        log_activity(
            organization=task.organization,
            user=request.user,
            action="ATTACHMENT_UPLOADED",
            entity=obj,
            metadata={"task_id": task.id, "project_id": task.project_id},
        )
        return Response(
            TaskAttachmentSerializer(obj, context={"request": request}).data, status=201
        )

    @action(detail=True, methods=["get"])
    def activities(self, request, pk=None):
        task = self.get_object()
        qs = (
            ActivityLog.objects.filter(organization=task.organization)
            .filter(
                Q(entity_type="Task", entity_id=task.id) | Q(metadata__task_id=task.id)
            )
            .select_related("user")[:50]
        )
        return Response(ActivitySerializer(qs, many=True).data)


class TaskLabelViewSet(viewsets.ModelViewSet):
    serializer_class = TaskLabelSerializer
    permission_classes = [IsAuthenticated, TaskAccessPermission]
    pagination_class = None

    def get_queryset(self):
        return TaskLabel.objects.filter(
            organization=current_membership(self.request).organization
        )

    def perform_create(self, s):
        s.save(organization=current_membership(self.request).organization)


class TaskCommentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated, TaskAccessPermission]

    def get_queryset(self):
        return TaskComment.objects.filter(
            task__in=TaskViewSet.base_queryset_for(self.request)
        ).select_related("author", "task")

    def perform_update(self, s):
        if s.instance.author_id != self.request.user.id:
            raise PermissionDenied("Somente o autor pode editar.")
        s.save()

    def perform_destroy(self, obj):
        m = current_membership(self.request)
        if obj.author_id != self.request.user.id and m.role not in ("OWNER", "ADMIN"):
            raise PermissionDenied("Sem permissão.")
        obj.delete()


class TaskAttachmentViewSet(viewsets.GenericViewSet):
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated, TaskAccessPermission]

    def get_queryset(self):
        return TaskAttachment.objects.filter(
            task__in=TaskViewSet.base_queryset_for(self.request)
        ).select_related("uploaded_by", "task")

    def destroy(self, request, pk=None):
        obj = self.get_object()
        m = current_membership(request)
        if obj.uploaded_by_id != request.user.id and m.role not in ("OWNER", "ADMIN"):
            return Response(status=403)
        task = obj.task
        obj.file.delete(save=False)
        obj.delete()
        log_activity(
            organization=task.organization,
            user=request.user,
            action="ATTACHMENT_REMOVED",
            entity=task,
            metadata={"task_id": task.id, "project_id": task.project_id},
        )
        return Response(status=204)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        obj = self.get_object()
        return FileResponse(
            obj.file.open("rb"),
            as_attachment=True,
            filename=obj.original_name,
            content_type=obj.content_type,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    m = current_membership(request)
    projects = Project.objects.filter(organization=m.organization)
    tasks = Task.objects.filter(organization=m.organization).exclude(
        status=Task.Status.DONE
    )
    if m.role == "MEMBER":
        projects = projects.filter(members__user=request.user)
        tasks = tasks.filter(project__members__user=request.user)
    recent = projects.select_related("client").order_by("-created_at")[:5]
    upcoming = (
        projects.filter(status__in=["ACTIVE", "PLANNING"], due_date__gte=date.today())
        .select_related("client")
        .order_by("due_date")[:5]
    )
    activities = ActivityLog.objects.filter(organization=m.organization).select_related(
        "user"
    )[:8]
    return Response(
        {
            "active_projects": projects.filter(status="ACTIVE").count(),
            "pending_tasks": tasks.distinct().count(),
            "hours_this_month": 0,
            "monthly_revenue": "0.00",
            "recent_projects": ProjectSerializer(
                recent, many=True, context={"request": request}
            ).data,
            "upcoming_deadlines": ProjectSerializer(
                upcoming, many=True, context={"request": request}
            ).data,
            "recent_activity": ActivitySerializer(activities, many=True).data,
            "has_clients": Client.objects.filter(organization=m.organization).exists(),
            "has_projects": projects.exists(),
            "profile_complete": bool(request.user.first_name and request.user.last_name and request.user.bio),
        }
    )
