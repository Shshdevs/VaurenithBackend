from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import InvalidService, ServiceName, SystemIdentifier
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


class ServiceData(Schema):
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    name: str
    slug: str
    service_type: ServiceType
    description: str | None
    system_identifier: str | None
    status: ResourceStatus
    last_status_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime


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


class ServiceUpdateRequest(Schema):
    version: int = Field(ge=1)
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


class ServiceStatusUpdateRequest(Schema):
    version: int = Field(ge=1)
    status: ResourceStatus
