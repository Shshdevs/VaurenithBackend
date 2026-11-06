from pydantic import Field, field_validator

from ....domain.identity.enums import PlatformType
from ....domain.identity.exceptions import InvalidEmail
from ....domain.identity.value_objects.email import EmailAddress
from ..common import Schema


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
