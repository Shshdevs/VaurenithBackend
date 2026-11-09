from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import DeviceName, InvalidDevice
from app.domain.infrastructure.enums import DeviceType


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
