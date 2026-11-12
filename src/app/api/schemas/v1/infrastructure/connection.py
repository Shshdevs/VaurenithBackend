from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.infrastructure import InvalidConnection
from app.domain.infrastructure.entities.connection import Connection
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus


class ConnectionData(Schema):
    id: UUID
    device_id: UUID
    name: str
    slug: str
    host: str
    port: int
    username: str
    authentication_type: AuthenticationType
    connection_timeout: int
    is_default: bool
    last_connected_at: datetime | None
    last_status: ConnectionStatus
    version: int
    created_at: datetime
    updated_at: datetime


class ConnectionCreateRequest(Schema):
    device_id: UUID
    name: str
    host: str
    port: int = Field(default=22, ge=1, le=65535)
    username: str
    authentication_type: AuthenticationType
    connection_timeout: int = Field(default=30, gt=0)
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return Connection._normalize_required_text(
                value, "name", Connection.MAX_NAME_LENGTH
            )
        except InvalidConnection as error:
            raise ValueError(str(error)) from error

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        try:
            return Connection._normalize_required_text(
                value, "username", Connection.MAX_USERNAME_LENGTH
            )
        except InvalidConnection as error:
            raise ValueError(str(error)) from error

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Connection host must be a string")
        value = value.strip()
        if not value or len(value) > Connection.MAX_HOST_LENGTH:
            raise ValueError("Connection host is invalid")
        return value


class ConnectionUpdateRequest(Schema):
    version: int = Field(ge=1)
    name: str
    host: str
    port: int = Field(ge=1, le=65535)
    username: str
    authentication_type: AuthenticationType
    connection_timeout: int = Field(gt=0)
    is_default: bool

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return Connection._normalize_required_text(
                value, "name", Connection.MAX_NAME_LENGTH
            )
        except InvalidConnection as error:
            raise ValueError(str(error)) from error

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        try:
            return Connection._normalize_required_text(
                value, "username", Connection.MAX_USERNAME_LENGTH
            )
        except InvalidConnection as error:
            raise ValueError(str(error)) from error

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Connection host must be a string")
        value = value.strip()
        if not value or len(value) > Connection.MAX_HOST_LENGTH:
            raise ValueError("Connection host is invalid")
        return value


class ConnectionStatusUpdateRequest(Schema):
    version: int = Field(ge=1)
    status: ConnectionStatus
    last_connected_at: datetime | None = None
    last_error: str | None = Field(default=None, max_length=4000)
