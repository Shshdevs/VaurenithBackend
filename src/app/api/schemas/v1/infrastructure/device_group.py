from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import DeviceGroupName, InvalidDeviceGroup


class DeviceGroup(Schema):
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    version: int


class DeviceGroupCreateRequest(Schema):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DeviceGroupName(value).value
        except InvalidDeviceGroup as error:
            raise ValueError(str(error)) from error


class DeviceGroupUpdateRequest(Schema):
    version: int = Field(ge=1, le=2**63 - 2)
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DeviceGroupName(value).value
        except InvalidDeviceGroup as error:
            raise ValueError(str(error)) from error
