from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_team_invitation_email(email, organization_name, token):
    url = f"{settings.FRONTEND_URL}/team-invitations/accept?token={token}"
    return send_mail(
        f"Convite para a equipe {organization_name}",
        f"Você foi convidado para trabalhar no DevFlow. Defina seu acesso: {url}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
