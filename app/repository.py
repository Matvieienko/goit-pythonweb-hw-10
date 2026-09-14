from datetime import date, timedelta

from sqlalchemy import and_, extract, or_, select
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas import ContactCreate, ContactUpdate


def get_contacts(
    db: Session,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    query = select(Contact).where(Contact.user_id == user_id)

    if first_name:
        query = query.where(
            Contact.first_name.icontains(first_name, autoescape=True)
        )
    if last_name:
        query = query.where(
            Contact.last_name.icontains(last_name, autoescape=True)
        )
    if email:
        query = query.where(Contact.email.icontains(email, autoescape=True))

    query = query.order_by(Contact.id).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_contact(
    db: Session,
    contact_id: int,
    user_id: int,
) -> Contact | None:
    query = select(Contact).where(
        Contact.id == contact_id,
        Contact.user_id == user_id,
    )
    return db.scalar(query)


def create_contact(
    db: Session,
    body: ContactCreate,
    user_id: int,
) -> Contact:
    contact = Contact(
        **body.model_dump(),
        user_id=user_id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(
    db: Session,
    contact_id: int,
    body: ContactUpdate,
    user_id: int,
) -> Contact | None:
    contact = get_contact(db, contact_id, user_id)
    if contact is None:
        return None

    for field, value in body.model_dump().items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(
    db: Session,
    contact_id: int,
    user_id: int,
) -> bool:
    contact = get_contact(db, contact_id, user_id)
    if contact is None:
        return False

    db.delete(contact)
    db.commit()
    return True


def get_upcoming_birthdays(
    db: Session,
    user_id: int,
) -> list[Contact]:
    today = date.today()
    upcoming_dates = [today + timedelta(days=offset) for offset in range(7)]

    conditions = [
        and_(
            extract("month", Contact.birthday) == day.month,
            extract("day", Contact.birthday) == day.day,
        )
        for day in upcoming_dates
    ]

    query = select(Contact).where(
        Contact.user_id == user_id,
        or_(*conditions),
    )
    contacts = list(db.scalars(query).all())

    date_order = {
        (day.month, day.day): index
        for index, day in enumerate(upcoming_dates)
    }

    return sorted(
        contacts,
        key=lambda contact: (
            date_order[(contact.birthday.month, contact.birthday.day)],
            contact.id,
        ),
    )