import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .messaging import MessagingNotConfigured, send_whatsapp

logger = logging.getLogger(__name__)


@shared_task
def deliver_invoice_payment(payment_id):
    from .models import InvoicePayment

    payment = InvoicePayment.objects.select_related("invoice__client").filter(pk=payment_id).first()
    if not payment:
        return {"email": False, "phone": False}
    invoice = payment.invoice
    client = invoice.client
    url = f"{settings.FRONTEND_URL}/pagar/{payment.public_token}"
    description = invoice.items.values_list("description", flat=True).first() or invoice.number
    message = (
        f"Cobrança {invoice.number}\nCliente: {client.name}\nDescrição: {description}\n"
        f"Valor: R$ {invoice.total}\nVencimento: {invoice.due_on:%d/%m/%Y}\n"
        f"Acesse o QR Code e o Pix Copia e Cola: {url}\nCódigo Pix: {payment.pix_code}"
    )
    email_sent = False
    if client.email:
        email_sent = bool(send_mail(
            f"Cobrança {invoice.number} - DevFlow",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [client.email],
            fail_silently=False,
        ))
    phone_sent = False
    if client.phone:
        try:
            phone_sent = send_whatsapp(phone=client.phone, message=message)
        except MessagingNotConfigured as exc:
            logger.info("Envio por telefone não realizado: %s", exc)
    return {"email": email_sent, "phone": phone_sent}
