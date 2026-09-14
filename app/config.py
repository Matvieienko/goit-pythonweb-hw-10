from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str = Field(min_length=32)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(gt=0)
    JWT_EMAIL_TOKEN_EXPIRE_MINUTES: int = Field(gt=0)

    APP_BASE_URL: str
    CORS_ORIGINS: list[str]

    REDIS_URL: str
    ME_RATE_LIMIT: str

    SMTP_HOST: str
    SMTP_PORT: int = Field(ge=1, le=65535)
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_START_TLS: bool
    SMTP_USE_TLS: bool
    MAIL_FROM: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()