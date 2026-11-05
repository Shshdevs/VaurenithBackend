from pydantic import Field, field_validator

from ....domain.identity.exceptions import InvalidEmail
from ....domain.identity.value_objects.email import EmailAddress
from ..common import Schema


class UserCreateRequest(Schema):
    email: str
    display_name: str | None = Field(default=None, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Email address is invalid")
        try:
            return EmailAddress(value).value
        except InvalidEmail as error:
            raise ValueError(str(error)) from error
