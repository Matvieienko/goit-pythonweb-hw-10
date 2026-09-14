from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from starlette.concurrency import run_in_threadpool

from app import user_repository
from app.cloudinary_service import upload_avatar
from app.config import settings
from app.dependencies import CurrentUser, DatabaseSession
from app.rate_limiter import limiter
from app.user_schemas import UserResponse


router = APIRouter(tags=["Users"])

MAX_AVATAR_SIZE = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.ME_RATE_LIMIT)
def read_me(
    request: Request,
    response: Response,
    user: CurrentUser,
):
    return user


@router.patch("/me/avatar", response_model=UserResponse)
async def update_user_avatar(
    db: DatabaseSession,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG and WebP images are allowed",
        )

    file_data = await file.read(MAX_AVATAR_SIZE + 1)

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty",
        )

    if len(file_data) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Avatar must not exceed 5 MB",
        )

    try:
        avatar_url = await run_in_threadpool(
            upload_avatar,
            file_data,
            user.id,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload avatar",
        ) from error
    finally:
        await file.close()

    return user_repository.update_avatar(db, user, avatar_url)