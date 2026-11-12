from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import DeviceName, InvalidDevice
from app.domain.infrastructure.enums import DeviceType


class Device(Schema):
    id: UUID
    user_id: UUID
    name: str
    slug: str
    hostname: str | None
    description: str | None
    device_type: DeviceType
    operating_system: str | None
    os_version: str | None
    architecture: str | None
    tags: list[str] | None
    last_seen_at: datetime | None
    last_status_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class DeviceCreateRequest(Schema):
    name: str
    device_type: DeviceType
    hostname: str | None = None
    description: str | None = None
    operating_system: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DeviceName(value).value
        except InvalidDevice as error:
            raise ValueError(str(error)) from error


class DeviceUpdateRequest(Schema):
    version: int = Field(ge=1)
    name: str
    device_type: DeviceType
    hostname: str | None = None
    description: str | None = None
    operating_system: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DeviceName(value).value
        except InvalidDevice as error:
            raise ValueError(str(error)) from error
