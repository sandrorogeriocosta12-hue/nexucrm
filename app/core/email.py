"""
Módulo de Email Transacional - Produção
Suporta: Resend, SendGrid, SMTP genérico
"""

import os
import logging
from typing import List, Optional
from typing import List, Optional

# EmailStr used later in type hints; define simple alias
from pydantic import EmailStr

logger = logging.getLogger(__name__)


class EmailSettings:
    """Configuração de email lida diretamente de variáveis de ambiente"""

    def __init__(self):
        self.RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
        self.SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
        self.SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
        self.SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
        self.SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() in (
            "1",
            "true",
            "yes",
        )
        self.EMAIL_FROM: EmailStr = os.getenv("EMAIL_FROM", "noreply@vexus-crm.com")
        self.EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Vexus CRM")


environment = EmailSettings()


class EmailService:
    """Facade for sending specific transactional emails"""

    @staticmethod
    def send_password_reset_email(
        email: str, name: str, reset_url: str, expires_in_hours: int = 24
    ) -> bool:
        subject = "Redefinição de senha"
        html = template_password_reset(reset_url)
        # run coroutine synchronously for simplicity
        try:
            return bool(__import__("asyncio").run(send_email([email], subject, html)))
        except Exception:
            return False

    @staticmethod
    def send_password_changed_email(email: str, name: str) -> bool:
        subject = "Senha alterada"
        html = f"<p>Olá {name}, sua senha foi alterada com sucesso.</p>"
        try:
            return bool(__import__("asyncio").run(send_email([email], subject, html)))
        except Exception:
            return False

    @staticmethod
    def send_account_deletion_email(email: str) -> bool:
        subject = "Conta deletada"
        html = "<p>Sua conta foi removida conforme solicitado. Lamentamos vê-lo ir embora.</p>"
        try:
            return bool(__import__("asyncio").run(send_email([email], subject, html)))
        except Exception:
            return False

    # Add other convenience methods as needed


async def send_email(
    to: List[EmailStr],
    subject: str,
    html: str,
    text: Optional[str] = None,
    reply_to: Optional[EmailStr] = None,
) -> bool:
    """Enviar email transacional"""

    try:
        if email_settings.RESEND_API_KEY:
            return await _send_via_resend(to, subject, html, text, reply_to)
        elif email_settings.SENDGRID_API_KEY:
            return await _send_via_sendgrid(to, subject, html, text, reply_to)
        elif email_settings.SMTP_HOST:
            return await _send_via_smtp(to, subject, html, text, reply_to)
        else:
            logger.warning("Nenhum provedor de email configurado")
            return False
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return False


async def _send_via_resend(
    to: List[EmailStr],
    subject: str,
    html: str,
    text: Optional[str],
    reply_to: Optional[EmailStr],
) -> bool:
    """Enviar via Resend API"""
    try:
        import resend

        resend.api_key = environment.RESEND_API_KEY

        params = {
            "from": f"{environment.EMAIL_FROM_NAME} <{environment.EMAIL_FROM}>",
            "to": to,
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text
        if reply_to:
            params["reply_to"] = reply_to

        response = resend.Emails.send(params)
        if response.get("id"):
            logger.info(f"Email enviado via Resend: {response['id']}")
            return True
        return False
    except Exception as e:
        logger.error(f"Erro Resend: {str(e)}")
        return False


async def _send_via_sendgrid(
    to: List[EmailStr],
    subject: str,
    html: str,
    text: Optional[str],
    reply_to: Optional[EmailStr],
) -> bool:
    """Enviar via SendGrid API"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = SendGridAPIClient(environment.SENDGRID_API_KEY)
        message = Mail(
            from_email=Email(environment.EMAIL_FROM, environment.EMAIL_FROM_NAME),
            to_emails=[To(addr) for addr in to],
            subject=subject,
            html_content=Content("text/html", html),
        )
        if text:
            message.plain_text_content = Content("text/plain", text)
        if reply_to:
            message.reply_to = Email(reply_to)

        response = sg.send(message)
        if response.status_code == 202:
            logger.info("Email enviado via SendGrid")
            return True
        return False
    except Exception as e:
        logger.error(f"Erro SendGrid: {str(e)}")
        return False


async def _send_via_smtp(
    to: List[EmailStr],
    subject: str,
    html: str,
    text: Optional[str],
    reply_to: Optional[EmailStr],
) -> bool:
    """Enviar via SMTP genérico"""
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        message = MIMEMultipart("alternative")
        message["From"] = f"{environment.EMAIL_FROM_NAME} <{environment.EMAIL_FROM}>"
        message["To"] = ", ".join(to)
        message["Subject"] = subject
        if reply_to:
            message["Reply-To"] = reply_to

        if text:
            message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        async with aiosmtplib.SMTP(
            hostname=environment.SMTP_HOST,
            port=environment.SMTP_PORT,
        ) as smtp:
            await smtp.login(environment.SMTP_USER, environment.SMTP_PASSWORD)
            await smtp.send_message(message)

        logger.info("Email enviado via SMTP")
        return True
    except Exception as e:
        logger.error(f"Erro SMTP: {str(e)}")
        return False


def template_verify_email(verify_link: str) -> str:
    """Template para verificação de email"""
    return f"""<html><body style="font-family: sans-serif;">
<div style="max-width: 500px; margin: 0 auto; padding: 20px;">
<h1 style="color: #4f46e5;">Bem-vindo ao Vexus CRM</h1>
<p>Verifique seu email clicando no botão abaixo:</p>
<a href="{verify_link}" style="background: #4f46e5; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block; margin: 20px 0;">Verificar Email</a>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
<p style="color: #999; font-size: 12px;">Vexus CRM</p>
</div></body></html>"""


def template_password_reset(reset_link: str) -> str:
    """Template HTML profissional para redefinição de senha."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:520px;margin:40px auto;background:#1e1b4b;border-radius:16px;overflow:hidden;border:1px solid #3730a3;">
    <div style="background:linear-gradient(135deg,#6d28d9,#7c3aed);padding:32px 36px;">
      <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">Nexus IA</h1>
      <p style="margin:6px 0 0;color:#c4b5fd;font-size:13px;">Sistema de Automação Inteligente</p>
    </div>
    <div style="padding:36px;">
      <h2 style="color:#e2e8f0;font-size:18px;font-weight:600;margin:0 0 16px;">Olá,</h2>
      <p style="color:#94a3b8;font-size:14px;line-height:1.7;margin:0 0 14px;">
        Recebemos uma solicitação para redefinir a senha da sua conta no
        <strong style="color:#c4b5fd;">Nexus CRM</strong>.
      </p>
      <p style="color:#94a3b8;font-size:14px;line-height:1.7;margin:0 0 28px;">
        Para escolher uma nova senha e restabelecer o seu acesso, clique no botão abaixo.
        Por motivos de segurança, este link é
        <strong style="color:#fbbf24;">válido por 1 hora</strong>.
      </p>
      <div style="text-align:center;margin:0 0 32px;">
        <a href="{reset_link}"
           style="background:#6d28d9;color:#fff;padding:14px 32px;text-decoration:none;
                  border-radius:8px;font-weight:700;font-size:15px;display:inline-block;">
          Redefinir Minha Senha
        </a>
      </div>
      <p style="color:#64748b;font-size:13px;line-height:1.6;font-style:italic;margin:0;">
        Se você não solicitou essa alteração, nenhuma ação é necessária e sua senha atual continuará segura.
      </p>
    </div>
    <div style="padding:20px 36px;border-top:1px solid #2d2d4a;">
      <p style="margin:0;color:#475569;font-size:12px;line-height:1.6;">
        Equipe de Segurança Nexus IA<br>Campos dos Goytacazes, RJ
      </p>
    </div>
  </div>
</body>
</html>"""


def template_invite(company_name: str, invite_link: str) -> str:
    """Template para convite"""
    return f"""<html><body style="font-family: sans-serif;">
<div style="max-width: 500px; margin: 0 auto; padding: 20px;">
<h1 style="color: #4f46e5;">Convite para {company_name}</h1>
<p>Você foi convidado. Clique para aceitar:</p>
<a href="{invite_link}" style="background: #4f46e5; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block; margin: 20px 0;">Aceitar Convite</a>
</div></body></html>"""
