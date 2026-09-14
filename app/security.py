from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.config import settings


ALGORITHM = "HS256"
TokenPurpose = Literal["access", "email_verification"]

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def _create_token(
    subject: str,
    purpose: TokenPurpose,
    expires_minutes: int,
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "purpose": purpose,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALGORITHM,
    )


def create_access_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        purpose="access",
        expires_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_email_verification_token(email: str) -> str:
    return _create_token(
        subject=email,
        purpose="email_verification",
        expires_minutes=settings.JWT_EMAIL_TOKEN_EXPIRE_MINUTES,
    )


def decode_token(token: str, expected_purpose: TokenPurpose) -> str:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "purpose", "iat", "exp"]},
    )

    if payload["purpose"] != expected_purpose:
        raise InvalidTokenError("Invalid token purpose")

    subject = payload["sub"]
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("Invalid token subject")

    return subject