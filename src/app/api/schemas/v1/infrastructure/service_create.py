from typing import Any
from uuid import UUID

from pydantic import field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import InvalidService, ServiceName, SystemIdentifier
from app.domain.infrastructure.enums import ServiceType


class ServiceCreateRequest(Schema):
    device_id: UUID
    project_id: UUID | None = None
    environment_id: UUID | None = None
    name: str
    service_type: ServiceType
    description: str | None = None
    system_identifier: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return ServiceName(value).value
        except InvalidService as error:
            raise ValueError(str(error)) from error

    @field_validator("system_identifier")
    @classmethod
    def validate_system_identifier(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        try:
            return SystemIdentifier(value).value
        except InvalidService as error:
            raise ValueError(str(error)) from error
