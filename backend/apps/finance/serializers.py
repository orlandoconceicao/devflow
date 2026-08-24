from django.db import transaction
from rest_framework import serializers

from apps.work.context import current_membership

from .models import Expense, Invoice, InvoiceItem, InvoicePayment, MemberRate, Revenue, TimeEntry


class TenantSerializer(serializers.ModelSerializer):
    def validate_project(self, value):
        if (
            value
            and value.organization_id
            != current_membership(self.context["request"]).organization_id
        ):
            raise serializers.ValidationError("Projeto inválido para este workspace.")
        return value


class MemberRateSerializer(TenantSerializer):
    class Meta:
        model = MemberRate
        fields = ("id", "user", "hourly_cost", "hourly_rate")

    def validate_user(self, value):
        org = current_membership(self.context["request"]).organization
        if not org.memberships.filter(user=value).exists():
            raise serializers.ValidationError("Usuário não pertence ao workspace.")
        return value


class TimeEntrySerializer(TenantSerializer):
    user_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TimeEntry
        fields = (
            "id",
            "project",
            "project_name",
            "task",
            "task_title",
            "user",
            "user_name",
            "description",
            "started_at",
            "ended_at",
            "duration_seconds",
            "hourly_rate",
            "hourly_cost",
            "billable",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "user",
            "duration_seconds",
            "hourly_rate",
            "hourly_cost",
            "created_at",
            "updated_at",
        )

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    def validate(self, data):
        project = data.get("project", getattr(self.instance, "project", None))
        task = data.get("task", getattr(self.instance, "task", None))
        start = data.get("started_at", getattr(self.instance, "started_at", None))
        end = data.get("ended_at", getattr(self.instance, "ended_at", None))
        if task and project and task.project_id != project.id:
            raise serializers.ValidationError(
                {"task": "A tarefa deve pertencer ao projeto."}
            )
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"ended_at": "O término deve ser posterior ao início."}
            )
        return data


class ExpenseSerializer(TenantSerializer):
    class Meta:
        model = Expense
        fields = (
            "id",
            "project",
            "description",
            "amount",
            "category",
            "occurred_on",
            "created_by",
            "created_at",
        )
        read_only_fields = ("created_by", "created_at")


class RevenueSerializer(TenantSerializer):
    class Meta:
        model = Revenue
        fields = (
            "id",
            "project",
            "client",
            "description",
            "amount",
            "occurred_on",
            "created_by",
            "created_at",
        )
        read_only_fields = ("created_by", "created_at")

    def validate_client(self, value):
        if (
            value
            and value.organization_id
            != current_membership(self.context["request"]).organization_id
        ):
            raise serializers.ValidationError("Cliente inválido.")
        return value


class InvoiceItemSerializer(serializers.ModelSerializer):
    time_entry_ids = serializers.PrimaryKeyRelatedField(
        source="time_entries",
        queryset=TimeEntry.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "description",
            "quantity",
            "unit_price",
            "total",
            "time_entry_ids",
        )
        read_only_fields = ("total",)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("A quantidade deve ser maior que zero.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value


class InvoiceSerializer(TenantSerializer):
    items = InvoiceItemSerializer(many=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "client",
            "client_name",
            "project",
            "number",
            "status",
            "issued_on",
            "due_on",
            "payment_release_on",
            "auto_generate_payment",
            "notes",
            "subtotal",
            "total",
            "paid_at",
            "items",
            "payment",
            "created_at",
        )
        read_only_fields = ("status", "subtotal", "total", "paid_at", "created_at")

    def get_payment(self, obj):
        payment = obj.payments.first()
        if not payment:
            return None
        return AdminPaymentSerializer(payment, context=self.context).data

    def validate_client(self, value):
        if (
            value.organization_id
            != current_membership(self.context["request"]).organization_id
        ):
            raise serializers.ValidationError("Cliente inválido.")
        return value

    def validate_project(self, value):
        if value and value.organization_id != current_membership(self.context["request"]).organization_id:
            raise serializers.ValidationError("Projeto inválido.")
        return value

    def validate(self, data):
        release = data.get(
            "payment_release_on", getattr(self.instance, "payment_release_on", None)
        )
        issued = data.get("issued_on", getattr(self.instance, "issued_on", None))
        if release and issued and release < issued:
            raise serializers.ValidationError(
                {"payment_release_on": "A liberação não pode anteceder a emissão."}
            )
        if not self.instance and not data.get("items"):
            raise serializers.ValidationError({"items": "Informe ao menos um item."})
        client = data.get("client", getattr(self.instance, "client", None))
        project = data.get("project", getattr(self.instance, "project", None))
        if project and client and project.client_id != client.id:
            raise serializers.ValidationError(
                {"project": "O projeto deve pertencer ao cliente selecionado."}
            )
        if data.get("due_on", getattr(self.instance, "due_on", None)) < data.get(
            "issued_on", getattr(self.instance, "issued_on", None)
        ):
            raise serializers.ValidationError(
                {"due_on": "O vencimento não pode anteceder a emissão."}
            )
        org = current_membership(self.context["request"]).organization
        for item in data.get("items", []):
            for entry in item.get("time_entries", []):
                if (
                    entry.organization_id != org.id
                    or not entry.billable
                    or entry.invoice_items.exclude(invoice=self.instance).exists()
                ):
                    raise serializers.ValidationError(
                        {"items": "Lançamento de horas inválido ou já faturado."}
                    )
        return data

    def _items(self, invoice, items):
        invoice.items.all().delete()
        subtotal = 0
        for item in items:
            entries = item.pop("time_entries", [])
            row = InvoiceItem.objects.create(invoice=invoice, **item)
            row.time_entries.set(entries)
            subtotal += row.total
        invoice.subtotal = invoice.total = subtotal
        invoice.save(update_fields=["subtotal", "total"])

    @transaction.atomic
    def create(self, data):
        items = data.pop("items", [])
        invoice = super().create(data)
        self._items(invoice, items)
        return invoice


class AdminPaymentSerializer(serializers.ModelSerializer):
    public_url = serializers.SerializerMethodField()

    class Meta:
        model = InvoicePayment
        fields = ("status", "expires_at", "public_url")

    def get_public_url(self, obj):
        return f"{__import__('django.conf', fromlist=['settings']).settings.FRONTEND_URL}/pagar/{obj.public_token}"


class PublicPaymentSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    client = serializers.CharField(source="invoice.client.name")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    due_date = serializers.DateField(source="invoice.due_on")
    qr_code = serializers.URLField(source="qr_code_url")

    class Meta:
        model = InvoicePayment
        fields = ("client", "description", "amount", "due_date", "status", "pix_code", "qr_code", "expires_at")

    def get_description(self, obj):
        item = obj.invoice.items.first()
        return item.description if item else f"Fatura {obj.invoice.number}"

    @transaction.atomic
    def update(self, instance, data):
        items = data.pop("items", None)
        invoice = super().update(instance, data)
        if items is not None:
            self._items(invoice, items)
        return invoice
