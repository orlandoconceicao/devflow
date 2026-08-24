import csv
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.work.context import current_membership

from .models import Expense, Invoice, MemberRate, Revenue, TimeEntry
from .serializers import (
    ExpenseSerializer,
    InvoiceSerializer,
    MemberRateSerializer,
    RevenueSerializer,
    TimeEntrySerializer,
)


class FinancePermission(BasePermission):
    def has_permission(self, request, view):
        return current_membership(request).role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        )


class WorkspaceStaffPermission(BasePermission):
    def has_permission(self, request, view):
        return current_membership(request).role != OrganizationMembership.Role.CLIENT


class TenantViewSet(viewsets.ModelViewSet):
    def org(self):
        return current_membership(self.request).organization

    def get_queryset(self):
        return self.queryset.filter(organization=self.org())

    def perform_create(self, s):
        s.save(organization=self.org(), created_by=self.request.user)


def filtered(qs, request, date_field):
    if request.query_params.get("start"):
        qs = qs.filter(**{date_field + "__gte": request.query_params["start"]})
    if request.query_params.get("end"):
        qs = qs.filter(**{date_field + "__lte": request.query_params["end"]})
    if request.query_params.get("project"):
        qs = qs.filter(project_id=request.query_params["project"])
    return qs


def rate_for(org, user):
    r = MemberRate.objects.filter(organization=org, user=user).first()
    return (r.hourly_rate, r.hourly_cost) if r else (Decimal("0"), Decimal("0"))


class MemberRateViewSet(TenantViewSet):
    queryset = MemberRate.objects.all()
    serializer_class = MemberRateSerializer
    permission_classes = [FinancePermission]

    def perform_create(self, s):
        s.save(organization=self.org())


class TimeEntryViewSet(TenantViewSet):
    queryset = TimeEntry.objects.select_related("project", "task", "user")
    serializer_class = TimeEntrySerializer
    permission_classes = [WorkspaceStaffPermission]

    def get_queryset(self):
        qs = filtered(super().get_queryset(), self.request, "started_at__date")
        if current_membership(self.request).role == OrganizationMembership.Role.MEMBER:
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, s):
        rate, cost = rate_for(self.org(), self.request.user)
        end = s.validated_data.get("ended_at")
        start = s.validated_data["started_at"]
        duration = max(0, int((end - start).total_seconds())) if end else 0
        s.save(
            organization=self.org(),
            user=self.request.user,
            hourly_rate=rate,
            hourly_cost=cost,
            duration_seconds=duration,
        )

    @action(detail=False, methods=["post"])
    def start(self, request):
        if TimeEntry.objects.filter(
            organization=self.org(), user=request.user, ended_at__isnull=True
        ).exists():
            return Response({"detail": "Já existe um timer ativo."}, status=409)
        data = {**request.data, "started_at": timezone.now()}
        s = self.get_serializer(data=data)
        s.is_valid(raise_exception=True)
        self.perform_create(s)
        return Response(s.data, status=201)

    @action(detail=False, methods=["get"])
    def active(self, request):
        row = self.get_queryset().filter(ended_at__isnull=True).first()
        return Response(self.get_serializer(row).data if row else None)

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        row = self.get_object()
        if row.ended_at:
            return Response({"detail": "Timer já encerrado."}, status=409)
        row.ended_at = timezone.now()
        row.duration_seconds = max(
            0, int((row.ended_at - row.started_at).total_seconds())
        )
        row.save(update_fields=["ended_at", "duration_seconds", "updated_at"])
        return Response(self.get_serializer(row).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset().filter(ended_at__isnull=False)
        seconds = qs.aggregate(v=Sum("duration_seconds"))["v"] or 0
        billable = sum(
            (Decimal(x.duration_seconds) / Decimal(3600)) * x.hourly_rate
            for x in qs
            if x.billable
        )
        return Response(
            {
                "seconds": seconds,
                "hours": round(seconds / 3600, 2),
                "billable_amount": billable,
            }
        )


class ExpenseViewSet(TenantViewSet):
    queryset = Expense.objects.select_related("project")
    serializer_class = ExpenseSerializer
    permission_classes = [FinancePermission]


class RevenueViewSet(TenantViewSet):
    queryset = Revenue.objects.select_related("project", "client")
    serializer_class = RevenueSerializer
    permission_classes = [FinancePermission]


class InvoiceViewSet(TenantViewSet):
    queryset = Invoice.objects.select_related("client").prefetch_related(
        "items__time_entries"
    )
    serializer_class = InvoiceSerializer
    permission_classes = [FinancePermission]

    @action(detail=True, methods=["post"], url_path="send")
    def send_invoice(self, request, pk=None):
        return self._status(self.get_object(), Invoice.Status.SENT)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        invoice.paid_at = timezone.now()
        return self._status(invoice, Invoice.Status.PAID)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._status(self.get_object(), Invoice.Status.CANCELLED)

    def _status(self, invoice, status):
        invoice.status = status
        invoice.save(update_fields=["status", "paid_at"])
        return Response(self.get_serializer(invoice).data)


@api_view(["GET"])
@permission_classes([FinancePermission])
def finance_dashboard(request):
    org = current_membership(request).organization
    start = request.query_params.get("start")
    end = request.query_params.get("end")
    revenue = (
        filtered(
            Revenue.objects.filter(organization=org), request, "occurred_on"
        ).aggregate(v=Sum("amount"))["v"]
        or 0
    )
    expenses = (
        filtered(
            Expense.objects.filter(organization=org), request, "occurred_on"
        ).aggregate(v=Sum("amount"))["v"]
        or 0
    )
    time_qs = filtered(
        TimeEntry.objects.filter(organization=org, ended_at__isnull=False),
        request,
        "started_at__date",
    )
    labor = sum(
        (Decimal(x.duration_seconds) / Decimal(3600)) * x.hourly_cost for x in time_qs
    )
    by_project = list(
        time_qs.values("project__name")
        .annotate(seconds=Sum("duration_seconds"))
        .order_by("-seconds")[:10]
    )
    return Response(
        {
            "revenue": revenue,
            "expenses": expenses,
            "labor_cost": labor,
            "profit": Decimal(revenue) - Decimal(expenses) - labor,
            "hours": round(sum(x.duration_seconds for x in time_qs) / 3600, 2),
            "by_project": by_project,
        }
    )


@api_view(["GET"])
@permission_classes([WorkspaceStaffPermission])
def reports(request):
    org = current_membership(request).organization
    qs = filtered(
        TimeEntry.objects.filter(organization=org, ended_at__isnull=False),
        request,
        "started_at__date",
    )
    group = request.query_params.get("group", "project")
    field = {
        "project": "project__name",
        "client": "project__client__name",
        "team": "user__email",
    }.get(group, "project__name")
    rows = list(
        qs.values(field).annotate(seconds=Sum("duration_seconds")).order_by("-seconds")
    )
    return Response(
        {
            "group": group,
            "rows": [
                {"name": r[field], "hours": round(r["seconds"] / 3600, 2)} for r in rows
            ],
        }
    )


@api_view(["GET"])
@permission_classes([WorkspaceStaffPermission])
def export_hours(request):
    org = current_membership(request).organization
    qs = filtered(
        TimeEntry.objects.filter(
            organization=org, ended_at__isnull=False
        ).select_related("project", "task", "user"),
        request,
        "started_at__date",
    )
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="horas.csv"'
    response.write("\ufeff")
    w = csv.writer(response)
    w.writerow(["Projeto", "Tarefa", "Pessoa", "Início", "Fim", "Horas", "Faturável"])
    for x in qs:
        w.writerow(
            [
                x.project.name,
                x.task.title if x.task else "",
                x.user.email,
                x.started_at.isoformat(),
                x.ended_at.isoformat(),
                round(x.duration_seconds / 3600, 2),
                "Sim" if x.billable else "Não",
            ]
        )
    return response
