from collections.abc import Callable
from functools import lru_cache
from typing import cast

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    auth_jwt_secret: SecretStr = Field(min_length=32)
    cors_origins: str
    api_prefix: str
    log_level: str
    max_request_body_size: int = Field(default=10 * 1024 * 1024, gt=0)
    database_connect_timeout: int = Field(default=5, gt=0)
    database_pool_size: int = Field(default=5, gt=0)
    database_max_overflow: int = Field(default=5, ge=0)
    database_pool_timeout: int = Field(default=10, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings_factory = cast(Callable[[], Settings], Settings)
    return settings_factory()
