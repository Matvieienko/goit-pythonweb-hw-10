from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password
from app.user_schemas import UserCreate


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    query = select(User).where(User.email == email)
    return db.scalar(query)


def get_user_by_username(db: Session, username: str) -> User | None:
    query = select(User).where(User.username == username)
    return db.scalar(query)


def create_user(db: Session, body: UserCreate) -> User:
    user = User(
        username=body.username,
        email=str(body.email),
        hashed_password=hash_password(body.password),
        email_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def mark_email_verified(db: Session, user: User) -> User:
    user.email_verified = True
    db.commit()
    db.refresh(user)
    return user


def update_avatar(db: Session, user: User, avatar_url: str) -> User:
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user