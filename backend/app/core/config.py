from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET", min_length=16)
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(14, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    cors_origins: str = Field("http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")

    seed_dev_data: bool = Field(False, alias="SEED_DEV_DATA")
    seed_user_email: str = Field("ashish@parasiteseo.ai", alias="SEED_USER_EMAIL")
    seed_user_password: str = Field("change-me-now", alias="SEED_USER_PASSWORD")

    openrouter_api_key: str | None = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    default_ai_model: str = Field("openai/gpt-4o-mini", alias="DEFAULT_AI_MODEL")
    ai_temperature: float = Field(0.3, alias="AI_TEMPERATURE", ge=0, le=2)
    ai_max_tokens: int = Field(8192, alias="AI_MAX_TOKENS", ge=256, le=32000)
    ai_timeout: float = Field(180.0, alias="AI_TIMEOUT", ge=5, le=600)
    ai_max_retries: int = Field(2, alias="AI_MAX_RETRIES", ge=0, le=5)
    ai_max_generation_chars: int = Field(120_000, alias="AI_MAX_GENERATION_CHARS", ge=1000)
    aws_access_key_id: str | None = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str | None = Field(None, alias="AWS_REGION")
    aws_s3_bucket: str | None = Field(None, alias="AWS_S3_BUCKET")
    seo_provider_api_key: str | None = Field(None, alias="SEO_PROVIDER_API_KEY")
    allow_http_links: bool = Field(False, alias="ALLOW_HTTP_LINKS")
    local_storage_root: str = Field("storage", alias="LOCAL_STORAGE_ROOT")
    public_app_url: str = Field("", alias="PUBLIC_APP_URL")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        url = value.strip()
        # Render and Heroku often inject postgres://, which SQLAlchemy rejects.
        if url.startswith("postgres://"):
            return "postgresql://" + url[len("postgres://") :]
        return url

    @field_validator("cors_origins")
    @classmethod
    def strip_origins(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
