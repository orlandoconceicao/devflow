from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_team_invitation_email(email, organization_name, token):
    url = f"{settings.FRONTEND_URL}/team-invitations/accept?token={token}"
    subject = f"Você foi convidado para a equipe {organization_name} no DevFlow"
    text_message = f"""Olá!

Você recebeu um convite para fazer parte da equipe {organization_name} no DevFlow.

Para aceitar o convite e configurar seu acesso, use o link abaixo:
{url}

Este convite é pessoal, pode ser utilizado apenas uma vez e expira em 7 dias. Se você não esperava receber este email, basta ignorá-lo.

Até breve,
Equipe DevFlow
"""
    safe_organization_name = escape(organization_name)
    safe_url = escape(url)
    html_message = f"""\
<!doctype html>
<html lang="pt-BR">
  <body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#172033">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:32px 16px">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #e4e9f2;overflow:hidden">
            <tr>
              <td style="padding:24px 32px;background:#172033;color:#ffffff;font-size:22px;font-weight:700">DevFlow</td>
            </tr>
            <tr>
              <td style="padding:36px 32px">
                <h1 style="margin:0 0 16px;font-size:26px;line-height:1.3;color:#172033">Você foi convidado!</h1>
                <p style="margin:0 0 12px;font-size:16px;line-height:1.6">Olá!</p>
                <p style="margin:0 0 24px;font-size:16px;line-height:1.6">
                  Você recebeu um convite para fazer parte da equipe <strong>{safe_organization_name}</strong> no DevFlow.
                </p>
                <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 28px">
                  <tr>
                    <td style="border-radius:8px;background:#2563eb">
                      <a href="{safe_url}" style="display:inline-block;padding:14px 24px;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700">Aceitar convite</a>
                    </td>
                  </tr>
                </table>
                <p style="margin:0 0 12px;font-size:14px;line-height:1.6;color:#596579">
                  Este convite é pessoal, pode ser utilizado apenas uma vez e expira em 7 dias.
                </p>
                <p style="margin:0;font-size:14px;line-height:1.6;color:#596579">
                  Se o botão não funcionar, copie e cole este endereço no navegador:<br>
                  <a href="{safe_url}" style="color:#2563eb;word-break:break-all">{safe_url}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;border-top:1px solid #e4e9f2;font-size:13px;line-height:1.5;color:#728096">
                Se você não esperava receber este email, basta ignorá-lo.<br>
                © DevFlow
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_message, "text/html")
    return message.send(fail_silently=False)
