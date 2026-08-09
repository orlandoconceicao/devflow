from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
@shared_task
def send_client_invitation_email(email,token):
    url=f"{settings.FRONTEND_URL}/client-invitations/accept?token={token}"; return send_mail("Convite para o portal DevFlow",f"Acesse seu projeto: {url}",settings.DEFAULT_FROM_EMAIL,[email],fail_silently=False)
@shared_task
def send_notification_email(notification_id):
    from .models import Notification
    n=Notification.objects.select_related("user").filter(pk=notification_id).first()
    return send_mail(n.title,n.message,settings.DEFAULT_FROM_EMAIL,[n.user.email],fail_silently=True) if n else 0
@shared_task
def remind_due_invoices():
    from apps.finance.models import Invoice
    from .models import ClientAccess,ReminderLog
    from .services import NotificationService
    due=timezone.localdate()+timezone.timedelta(days=3); count=0
    for invoice in Invoice.objects.filter(due_on=due,status__in=["DRAFT","SENT"]):
        log,created=ReminderLog.objects.get_or_create(invoice=invoice,reminder_date=timezone.localdate())
        if not created:continue
        for access in ClientAccess.objects.filter(client=invoice.client).select_related("user"):
            NotificationService.notify(organization=invoice.organization,user=access.user,type="INVOICE_DUE",title="Fatura próxima do vencimento",message=f"A fatura {invoice.number} vence em 3 dias.")
        count+=1
    return count
