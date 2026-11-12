from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.identity.enums import ClientDeviceStatus, PlatformType
from app.domain.identity.exceptions import InvalidEmail
from app.domain.identity.value_objects.email import EmailAddress


class UserData(Schema):
    id: UUID
    email: str
    display_name: str | None
    nickname: str
    auth_provider: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        email = value.value if isinstance(value, EmailAddress) else value
        if not isinstance(email, str):
            raise ValueError("Email address is invalid")
        try:
            return EmailAddress(email).value
        except InvalidEmail as error:
            raise ValueError(str(error)) from error


class UserCreateRequest(Schema):
    email: str
    display_name: str | None = Field(default=None, max_length=255)
    device_name: str = Field(min_length=1, max_length=255)
    platform: PlatformType
    app_version: str | None = Field(default=None, max_length=50)

    @field_validator("device_name")
    @classmethod
    def validate_device_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Device name is invalid")
        return normalized

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Email address is invalid")
        try:
            return EmailAddress(value).value
        except InvalidEmail as error:
            raise ValueError(str(error)) from error


class ClientDeviceRegisterRequest(Schema):
    name: str = Field(min_length=1, max_length=255)
    platform: PlatformType
    app_version: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Device name is invalid")
        return normalized


class ClientDeviceUpdateRequest(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    app_version: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Device name is invalid")
        return normalized


class ClientDeviceStatusRequest(Schema):
    status: Literal[ClientDeviceStatus.ACTIVE, ClientDeviceStatus.INACTIVE]


class ClientDeviceData(Schema):
    id: UUID
    name: str
    platform: PlatformType
    app_version: str | None
    status: ClientDeviceStatus
    registered_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None


class SessionData(Schema):
    id: UUID
    client_device_id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
