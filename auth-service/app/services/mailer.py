import smtplib
from email.message import EmailMessage

from app.config import get_settings


def send_reset_email(email: str, link: str) -> None:
    
    settings = get_settings()

    mensagem = EmailMessage()
    mensagem["Subject"] = "Redefinição de senha — Catálogo de Filmes"
    mensagem["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    mensagem["To"] = email
    mensagem.set_content(
        "Recebemos um pedido para redefinir sua senha.\n\n"
        f"Clique no link abaixo para criar uma nova senha (válido por 30 minutos):\n{link}\n\n"
        "Se você não pediu isso, ignore este e-mail."
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(mensagem)
    except (smtplib.SMTPException, OSError) as erro:
        print(f"[mailer] falha ao enviar e-mail de redefinição para {email}: {erro}", flush=True)
