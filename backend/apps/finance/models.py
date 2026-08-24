import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class MemberRate(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="member_rates",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="work_rates"
    )
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_member_rate"
            )
        ]


class TimeEntry(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="time_entries",
    )
    project = models.ForeignKey(
        "work.Project", on_delete=models.CASCADE, related_name="time_entries"
    )
    task = models.ForeignKey(
        "work.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="time_entries"
    )
    description = models.CharField(max_length=240, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                condition=Q(ended_at__isnull=True),
                name="one_active_timer_per_org_user",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "started_at"]),
            models.Index(fields=["organization", "project"]),
        ]


class Expense(models.Model):
    class Category(models.TextChoices):
        SOFTWARE = "SOFTWARE", "Software"
        PEOPLE = "PEOPLE", "Pessoas"
        TAX = "TAX", "Impostos"
        MARKETING = "MARKETING", "Marketing"
        OTHER = "OTHER", "Outros"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="expenses"
    )
    project = models.ForeignKey(
        "work.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER
    )
    occurred_on = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class Revenue(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="revenues"
    )
    project = models.ForeignKey(
        "work.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenues",
    )
    client = models.ForeignKey(
        "work.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revenues",
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    occurred_on = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    invoice = models.OneToOneField(
        "Invoice",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="revenue",
    )


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        SENT = "SENT", "Enviada"
        PAID = "PAID", "Paga"
        CANCELLED = "CANCELLED", "Cancelada"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="invoices"
    )
    client = models.ForeignKey(
        "work.Client", on_delete=models.PROTECT, related_name="invoices"
    )
    project = models.ForeignKey(
        "work.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    number = models.CharField(max_length=30)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    issued_on = models.DateField()
    due_on = models.DateField()
    payment_release_on = models.DateField(null=True, blank=True)
    auto_generate_payment = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "number"], name="unique_invoice_number"
            )
        ]
        ordering = ["-issued_on", "-id"]


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=240)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    time_entries = models.ManyToManyField(
        TimeEntry, blank=True, related_name="invoice_items"
    )

    def save(self, *args, **kwargs):
        self.total = (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))
        super().save(*args, **kwargs)


class InvoicePayment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Aguardando pagamento"
        PAID = "PAID", "Pago"
        EXPIRED = "EXPIRED", "Expirado"
        CANCELLED = "CANCELLED", "Cancelado"
        FAILED = "FAILED", "Falhou"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="payments"
    )
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    provider = models.CharField(max_length=20, default="mercado_pago")
    provider_payment_id = models.CharField(max_length=120, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    pix_code = models.TextField()
    qr_code = models.TextField()
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["invoice", "status"])]


class InvoicePaymentEvent(models.Model):
    provider = models.CharField(max_length=20, default="mercado_pago")
    provider_event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=80)
    payment = models.ForeignKey(
        InvoicePayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    processed_at = models.DateTimeField(auto_now_add=True)
