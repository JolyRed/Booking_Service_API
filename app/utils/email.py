import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_email(to_email: str, subject: str, body_html: str) -> bool:
    try:
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
        message["To"] = to_email
        message["Subject"] = subject

        html_part = MIMEText(body_html, "html")
        message.attach(html_part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)

        print(f"Email отправлен: {to_email}")
        return True

    except Exception as e:
        print(f"Ошибка: {e}")
        return False
