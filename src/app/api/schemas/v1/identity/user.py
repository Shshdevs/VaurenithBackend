from datetime import datetime
from uuid import UUID

from pydantic import field_validator

from .....domain.identity.exceptions import InvalidEmail
from .....domain.identity.value_objects.email import EmailAddress
from ...common import Schema


class UserData(Schema):
    id: UUID
    email: str
    display_name: str | None
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
