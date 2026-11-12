from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.projects.enums import EnvironmentType
from app.domain.projects.exceptions import InvalidEnvironment
from app.domain.projects.value_objects import EnvironmentName


class EnvironmentData(Schema):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    environment_type: EnvironmentType
    description: str | None
    configuration: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class EnvironmentCreateRequest(Schema):
    name: str
    environment_type: EnvironmentType = EnvironmentType.OTHER
    description: str | None = None
    configuration: dict[str, Any] | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return EnvironmentName(value).value
        except InvalidEnvironment as error:
            raise ValueError(str(error)) from error


class EnvironmentUpdateRequest(Schema):
    name: str
    environment_type: EnvironmentType
    description: str | None = None
    configuration: dict[str, Any] | None = None
    version: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return EnvironmentName(value).value
        except InvalidEnvironment as error:
            raise ValueError(str(error)) from error
