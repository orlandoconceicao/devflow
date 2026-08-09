from django.contrib import admin

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


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "status", "created_at")
    search_fields = ("name", "company", "email")
    list_filter = ("status", "organization")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "client", "status", "priority", "progress")
    search_fields = ("name", "client__name")
    list_filter = ("status", "priority", "organization")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role", "joined_at")
    list_filter = ("role",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "organization", "created_at")
    list_filter = ("action", "entity_type")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "position", "due_date")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "organization")


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "color")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "task", "uploaded_by", "file_size", "created_at")
