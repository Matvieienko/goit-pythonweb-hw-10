from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import IntegrityError

from app import user_repository
from app.dependencies import DatabaseSession
from app.email_service import send_verification_email
from app.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.user_schemas import (
    EmailVerificationRequest,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])

DUMMY_PASSWORD_HASH = hash_password("Unused dummy password")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    db: DatabaseSession,
):
    try:
        user = user_repository.create_user(db, body)
    except IntegrityError as error:
        db.rollback()
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already registered",
            ) from error
        raise

    background_tasks.add_task(send_verification_email, user.email)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DatabaseSession,
):
    user = user_repository.get_user_by_username(db, form_data.username)

    stored_hash = (
        user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
    )
    password_valid = verify_password(form_data.password, stored_hash)

    if user is None or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(
    token: Annotated[str, Query(min_length=1)],
    db: DatabaseSession,
):
    try:
        email = decode_token(
            token,
            expected_purpose="email_verification",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        ) from None

    user = user_repository.get_user_by_email(db, email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.email_verified:
        return MessageResponse(detail="Email already verified")

    user_repository.mark_email_verified(db, user)
    return MessageResponse(detail="Email successfully verified")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    body: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseSession,
):
    user = user_repository.get_user_by_email(db, str(body.email))

    if user is not None and not user.email_verified:
        background_tasks.add_task(send_verification_email, user.email)

    return MessageResponse(
        detail=(
            "If the account exists and requires verification, "
            "a verification email will be sent"
        )
    )