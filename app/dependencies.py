from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token
from app.user_repository import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        subject = decode_token(token, expected_purpose="access")
        user_id = int(subject)

        if user_id <= 0 or user_id > 2147483647:
            raise ValueError("Invalid user ID")
    except (InvalidTokenError, ValueError):
        raise credentials_error from None

    user = get_user_by_id(db, user_id)

    if user is None:
        raise credentials_error

    return user


def get_verified_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
VerifiedUser = Annotated[User, Depends(get_verified_user)]