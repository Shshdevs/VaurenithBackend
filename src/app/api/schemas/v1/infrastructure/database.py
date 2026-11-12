from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import (
    DatabaseCatalogName,
    DatabaseResourceName,
    InvalidDatabase,
)
from app.domain.infrastructure.enums import DbmsType, ResourceStatus


class DatabaseData(Schema):
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    container_id: UUID | None
    service_id: UUID | None
    name: str
    slug: str
    dbms_type: DbmsType
    host: str | None
    port: int | None
    database_name: str | None
    status: ResourceStatus
    last_checked_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime


class DatabaseCreateRequest(Schema):
    device_id: UUID
    name: str
    dbms_type: DbmsType
    project_id: UUID | None = None
    environment_id: UUID | None = None
    container_id: UUID | None = None
    service_id: UUID | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    database_name: str | None = None
    status: ResourceStatus = ResourceStatus.UNKNOWN
    last_checked_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DatabaseResourceName(value).value
        except InvalidDatabase as error:
            raise ValueError(str(error)) from error

    @field_validator("database_name")
    @classmethod
    def validate_database_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return DatabaseCatalogName(value).value
        except InvalidDatabase as error:
            raise ValueError(str(error)) from error


class DatabaseUpdateRequest(Schema):
    version: int = Field(ge=1)
    device_id: UUID
    name: str
    dbms_type: DbmsType
    status: ResourceStatus
    project_id: UUID | None = None
    environment_id: UUID | None = None
    container_id: UUID | None = None
    service_id: UUID | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    database_name: str | None = None
    last_checked_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return DatabaseResourceName(value).value
        except InvalidDatabase as error:
            raise ValueError(str(error)) from error

    @field_validator("database_name")
    @classmethod
    def validate_database_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return DatabaseCatalogName(value).value
        except InvalidDatabase as error:
            raise ValueError(str(error)) from error
