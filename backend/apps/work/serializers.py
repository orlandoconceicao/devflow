from pathlib import Path

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.organizations.models import OrganizationMembership

from .context import current_membership
from .models import (
    ActivityLog,
    Client,
    Project,
    ProjectMember,
    Task,
    TaskAssignee,
    TaskAttachment,
    TaskComment,
    TaskLabel,
)


class ClientSerializer(serializers.ModelSerializer):
    project_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "company",
            "document",
            "website",
            "notes",
            "status",
            "project_count",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source="user", read_only=True)

    class Meta:
        model = ProjectMember
        fields = ("id", "user", "user_detail", "role", "joined_at")
        read_only_fields = ("joined_at",)

    def validate_user(self, user):
        project = self.context["project"]
        if not OrganizationMembership.objects.filter(
            organization=project.organization, user=user
        ).exists():
            raise serializers.ValidationError(
                "O usuário não pertence ao workspace do projeto."
            )
        return user


class ProjectSerializer(serializers.ModelSerializer):
    client_detail = ClientSerializer(source="client", read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    created_by_detail = UserSerializer(source="created_by", read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "client",
            "client_detail",
            "name",
            "description",
            "status",
            "priority",
            "start_date",
            "due_date",
            "progress",
            "budget",
            "members",
            "created_by",
            "created_by_detail",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("progress", "created_by", "created_at", "updated_at")

    def validate_client(self, client):
        if (
            client.organization_id
            != current_membership(self.context["request"]).organization_id
        ):
            raise serializers.ValidationError("Cliente inválido para este workspace.")
        return client

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        due = data.get("due_date", getattr(self.instance, "due_date", None))
        if start and due and due < start:
            raise serializers.ValidationError(
                {"due_date": "O prazo não pode ser anterior à data inicial."}
            )
        return data


class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "user",
            "action",
            "entity_type",
            "entity_id",
            "metadata",
            "created_at",
        )


class TaskLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLabel
        fields = ("id", "name", "color", "created_at")
        read_only_fields = ("created_at",)

    def validate_color(self, value):
        import re

        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise serializers.ValidationError("Use uma cor hexadecimal válida.")
        return value.upper()


class TaskAssigneeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskAssignee
        fields = ("id", "user", "assigned_at")


class TaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignees = TaskAssigneeSerializer(many=True, read_only=True)
    labels = TaskLabelSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(read_only=True, default=0)
    attachments_count = serializers.IntegerField(read_only=True, default=0)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "status",
            "priority",
            "position",
            "due_date",
            "completed_at",
            "assignees",
            "labels",
            "comments_count",
            "attachments_count",
            "is_overdue",
            "created_at",
            "updated_at",
        )

    def get_is_overdue(self, obj):
        return bool(
            obj.due_date
            and obj.due_date < timezone.localdate()
            and obj.status != Task.Status.DONE
        )


class TaskSerializer(TaskListSerializer):
    assignee_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    label_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    created_by = UserSerializer(read_only=True)

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + (
            "assignee_ids",
            "label_ids",
            "created_by",
        )

    def validate_project(self, project):
        membership = current_membership(self.context["request"])
        if project.organization_id != membership.organization_id:
            raise serializers.ValidationError("Projeto inválido para este workspace.")
        if (
            membership.role == OrganizationMembership.Role.MEMBER
            and not project.members.filter(user=self.context["request"].user).exists()
        ):
            raise serializers.ValidationError("Você não participa deste projeto.")
        return project

    def validate(self, data):
        project = data.get("project", getattr(self.instance, "project", None))
        assignees = data.get("assignee_ids", [])
        labels = data.get("label_ids", [])
        if project and assignees:
            valid = set(
                project.members.filter(user_id__in=assignees).values_list(
                    "user_id", flat=True
                )
            )
            if valid != set(assignees):
                raise serializers.ValidationError(
                    {
                        "assignee_ids": "Todos os responsáveis devem ser membros do projeto."
                    }
                )
        if (
            project
            and labels
            and TaskLabel.objects.filter(id__in=labels)
            .exclude(organization=project.organization)
            .exists()
        ):
            raise serializers.ValidationError(
                {"label_ids": "Label inválida para este workspace."}
            )
        return data

    def _relations(self, task, assignees, labels):
        if assignees is not None:
            task.assignees.exclude(user_id__in=assignees).delete()
            for user_id in assignees:
                TaskAssignee.objects.get_or_create(task=task, user_id=user_id)
        if labels is not None:
            task.labels.set(labels)

    def create(self, data):
        assignees = data.pop("assignee_ids", [])
        labels = data.pop("label_ids", [])
        task = super().create(data)
        self._relations(task, assignees, labels)
        return task

    def update(self, instance, data):
        assignees = data.pop("assignee_ids", None)
        labels = data.pop("label_ids", None)
        task = super().update(instance, data)
        self._relations(task, assignees, labels)
        return task


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ("id", "task", "author", "content", "created_at", "updated_at")
        read_only_fields = ("task", "author", "created_at", "updated_at")

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("O comentário não pode ficar vazio.")
        return value.strip()


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskAttachment
        fields = (
            "id",
            "task",
            "uploaded_by",
            "file",
            "original_name",
            "file_size",
            "content_type",
            "created_at",
            "download_url",
        )
        read_only_fields = (
            "task",
            "uploaded_by",
            "original_name",
            "file_size",
            "content_type",
            "created_at",
            "download_url",
        )
        extra_kwargs = {"file": {"write_only": True}}

    def get_download_url(self, obj):
        return (
            self.context["request"].build_absolute_uri(
                f"/api/task-attachments/{obj.id}/download/"
            )
            if self.context.get("request")
            else None
        )

    def validate_file(self, file):
        allowed_ext = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".txt",
            ".docx",
            ".xlsx",
        }
        allowed_mime = {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/webp",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("O arquivo excede o limite de 10 MB.")
        if Path(file.name).suffix.lower() not in allowed_ext:
            raise serializers.ValidationError("Tipo de arquivo não permitido.")
        if getattr(file, "content_type", "") not in allowed_mime:
            raise serializers.ValidationError("Conteúdo do arquivo não permitido.")
        return file
