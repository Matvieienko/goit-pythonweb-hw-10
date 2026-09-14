from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status
from sqlalchemy.exc import IntegrityError

from app import repository
from app.dependencies import DatabaseSession, VerifiedUser
from app.schemas import ContactCreate, ContactResponse, ContactUpdate


router = APIRouter(prefix="/contacts", tags=["Contacts"])

ContactId = Annotated[int, Path(gt=0, le=2147483647)]


@router.get("/", response_model=list[ContactResponse])
def read_contacts(
    db: DatabaseSession,
    user: VerifiedUser,
    first_name: Annotated[str | None, Query(max_length=50)] = None,
    last_name: Annotated[str | None, Query(max_length=50)] = None,
    email: Annotated[str | None, Query(max_length=254)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return repository.get_contacts(
        db,
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        skip=skip,
        limit=limit,
    )


@router.get("/birthdays", response_model=list[ContactResponse])
def read_upcoming_birthdays(
    db: DatabaseSession,
    user: VerifiedUser,
):
    return repository.get_upcoming_birthdays(db, user_id=user.id)


@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(
    contact_id: ContactId,
    db: DatabaseSession,
    user: VerifiedUser,
):
    contact = repository.get_contact(db, contact_id, user_id=user.id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    body: ContactCreate,
    db: DatabaseSession,
    user: VerifiedUser,
):
    try:
        return repository.create_contact(db, body, user_id=user.id)
    except IntegrityError as error:
        db.rollback()
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contact with this email already exists",
            ) from error
        raise


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: ContactId,
    body: ContactUpdate,
    db: DatabaseSession,
    user: VerifiedUser,
):
    try:
        contact = repository.update_contact(
            db,
            contact_id,
            body,
            user_id=user.id,
        )
    except IntegrityError as error:
        db.rollback()
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contact with this email already exists",
            ) from error
        raise

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_contact(
    contact_id: ContactId,
    db: DatabaseSession,
    user: VerifiedUser,
):
    deleted = repository.delete_contact(db, contact_id, user_id=user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)