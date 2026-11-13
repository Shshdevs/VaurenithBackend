from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import cast

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    auth_jwt_issuer: str = Field(min_length=1)
    auth_jwt_audience: str = Field(min_length=1)
    auth_jwt_public_key_path: Path = Field(repr=False)
    auth_jwt_clock_skew_seconds: int = Field(ge=0, le=60)
    auth_jwt_max_lifetime_seconds: int = Field(gt=0, le=86400)
    cors_origins: str
    api_prefix: str
    log_level: str
    max_request_body_size: int = Field(default=10 * 1024 * 1024, gt=0)
    database_connect_timeout: int = Field(default=5, gt=0)
    database_pool_size: int = Field(default=5, gt=0)
    database_max_overflow: int = Field(default=5, ge=0)
    database_pool_timeout: int = Field(default=10, gt=0)
    _auth_jwt_public_key: str = PrivateAttr(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        if not self.auth_jwt_issuer.strip() or not self.auth_jwt_audience.strip():
            raise ValueError("AUTH_JWT_ISSUER and AUTH_JWT_AUDIENCE must not be blank")
        pem = self.auth_jwt_public_key_path.read_text(encoding="ascii")
        if "PRIVATE KEY" in pem:
            raise ValueError(
                "AUTH_JWT_PUBLIC_KEY_PATH must not contain private key material"
            )
        public_key = serialization.load_pem_public_key(pem.encode())
        if not isinstance(public_key, RSAPublicKey):
            raise ValueError("AUTH_JWT_PUBLIC_KEY_PATH must point to an RSA public key")
        if public_key.key_size < 2048:
            raise ValueError("AUTH_JWT_PUBLIC_KEY_PATH must point to at least 2048-bit RSA")
        self._auth_jwt_public_key = pem

    @property
    def auth_jwt_public_key(self) -> str:
        return self._auth_jwt_public_key

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings_factory = cast(Callable[[], Settings], Settings)
    return settings_factory()
