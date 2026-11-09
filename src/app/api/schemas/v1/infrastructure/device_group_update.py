from pydantic import field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import DeviceGroupName, InvalidDeviceGroup


class DeviceGroupUpdateRequest(Schema):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DeviceGroupName(value).value
        except InvalidDeviceGroup as error:
            raise ValueError(str(error)) from error
