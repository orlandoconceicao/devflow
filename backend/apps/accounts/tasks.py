from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(
    autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3}
)
def send_password_reset_email(email, uid, token):
    url = f"{settings.FRONTEND_URL}/password-reset/confirm?uid={uid}&token={token}"
    return send_mail(
        "Redefinição de senha DevFlow",
        f"Use este link para criar uma nova senha: {url}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
