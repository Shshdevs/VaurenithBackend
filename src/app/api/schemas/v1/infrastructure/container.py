from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import (
    ContainerImage,
    ContainerName,
    ContainerRuntimeId,
    InvalidContainer,
)
from app.domain.infrastructure.enums import ContainerStatus


class ContainerData(Schema):
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    service_id: UUID | None
    container_runtime_id: str
    name: str
    slug: str
    image: str | None
    status: ContainerStatus
    ports: dict[str, Any] | None
    volumes: dict[str, Any] | None
    networks: dict[str, Any] | None
    started_at: datetime | None
    last_seen_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime


class ContainerCreateRequest(Schema):
    device_id: UUID
    container_runtime_id: str
    name: str
    project_id: UUID | None = None
    environment_id: UUID | None = None
    service_id: UUID | None = None
    image: str | None = None
    status: ContainerStatus = ContainerStatus.UNKNOWN
    ports: dict[str, Any] | None = None
    volumes: dict[str, Any] | None = None
    networks: dict[str, Any] | None = None
    started_at: datetime | None = None
    last_seen_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("container_runtime_id")
    @classmethod
    def validate_container_runtime_id(cls, value: str) -> str:
        try:
            return ContainerRuntimeId(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return ContainerName(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return ContainerImage(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error


class ContainerUpdateRequest(Schema):
    version: int = Field(ge=1)
    device_id: UUID
    container_runtime_id: str
    name: str
    status: ContainerStatus
    project_id: UUID | None = None
    environment_id: UUID | None = None
    service_id: UUID | None = None
    image: str | None = None
    ports: dict[str, Any] | None = None
    volumes: dict[str, Any] | None = None
    networks: dict[str, Any] | None = None
    started_at: datetime | None = None
    last_seen_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("container_runtime_id")
    @classmethod
    def validate_container_runtime_id(cls, value: str) -> str:
        try:
            return ContainerRuntimeId(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return ContainerName(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return ContainerImage(value).value
        except InvalidContainer as error:
            raise ValueError(str(error)) from error
