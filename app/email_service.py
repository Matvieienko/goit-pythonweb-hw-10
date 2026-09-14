from email.message import EmailMessage
from urllib.parse import urlencode

import aiosmtplib

from app.config import settings
from app.security import create_email_verification_token


async def send_verification_email(email: str) -> None:
    token = create_email_verification_token(email)

    query = urlencode({"token": token})
    verification_url = (
        f"{settings.APP_BASE_URL.rstrip('/')}"
        f"/auth/verify-email?{query}"
    )

    message = EmailMessage()
    message["From"] = settings.MAIL_FROM
    message["To"] = email
    message["Subject"] = "Confirm your email — Contacts API"
    message.set_content(
        "Welcome to Contacts API!\n\n"
        "Confirm your email by opening this link:\n"
        f"{verification_url}\n\n"
        "This link is valid for "
        f"{settings.JWT_EMAIL_TOKEN_EXPIRE_MINUTES} minutes.\n"
        "If you did not register, you can ignore this email.\n"
    )

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=settings.SMTP_START_TLS,
        use_tls=settings.SMTP_USE_TLS,
        timeout=10,
    )