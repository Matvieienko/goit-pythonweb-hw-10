from typing import Any

import cloudinary
import cloudinary.uploader

from app.config import settings


cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_avatar(file_data: bytes, user_id: int) -> str:
    result: dict[str, Any] = cloudinary.uploader.upload(
        file_data,
        public_id=f"contacts_api/avatars/user_{user_id}",
        overwrite=True,
        invalidate=True,
        resource_type="image",
        transformation=[
            {
                "width": 250,
                "height": 250,
                "crop": "fill",
                "gravity": "face",
            }
        ],
    )

    secure_url = result.get("secure_url")

    if not isinstance(secure_url, str) or not secure_url:
        raise RuntimeError("Cloudinary did not return an avatar URL")

    return secure_url