from django.conf import settings
from django.db import models


class ClientAccess(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        "work.Client", on_delete=models.CASCADE, related_name="portal_accesses"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_accesses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["client", "user"], name="unique_client_user_access"
            )
        ]


class ClientInvitation(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        "work.Client", on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="client_invitations_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class ProjectDeliverable(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        READY_FOR_REVIEW = "READY_FOR_REVIEW", "Aguardando aprovação"
        APPROVED = "APPROVED", "Aprovada"
        CHANGES_REQUESTED = "CHANGES_REQUESTED", "Alterações solicitadas"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        "work.Project", on_delete=models.CASCADE, related_name="deliverables"
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.DRAFT
    )
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DeliverableComment(models.Model):
    deliverable = models.ForeignKey(
        ProjectDeliverable, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class DeliverableAttachment(models.Model):
    deliverable = models.ForeignKey(
        ProjectDeliverable, on_delete=models.CASCADE, related_name="attachments"
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to="deliverables/%Y/%m/")
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=40)
    title = models.CharField(max_length=160)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at", "created_at"])]


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)


class ReminderLog(models.Model):
    invoice = models.ForeignKey("finance.Invoice", on_delete=models.CASCADE)
    reminder_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "reminder_date"], name="unique_invoice_reminder_day"
            )
        ]
