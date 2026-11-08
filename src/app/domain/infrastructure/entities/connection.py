from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus
from app.domain.infrastructure.exceptions import InvalidConnection
from app.domain.infrastructure.value_objects import ConnectionEndpoint


class Connection(Entity):
    """Connection metadata only.
    Passwords and private keys are stored in client Secure Storage."""

    MAX_NAME_LENGTH = 255
    MAX_HOST_LENGTH = 512
    MAX_USERNAME_LENGTH = 255

    def __init__(
        self,
        entity_id: EntityId,
        device_id: EntityId,
        name: str,
        host: str,
        username: str,
        authentication_type: AuthenticationType,
        created_at: datetime,
        updated_at: datetime,
        port: int = 22,
        connection_timeout: int = 30,
        is_default: bool = False,
        last_connected_at: datetime | None = None,
        last_status: ConnectionStatus = ConnectionStatus.UNKNOWN,
        last_error: str | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(device_id, UUID):
            raise InvalidConnection("Connection and device identifiers must be UUIDs")
        normalized_name = self._normalize_required_text(name, "name", self.MAX_NAME_LENGTH)
        endpoint = ConnectionEndpoint(host=host, port=port)
        normalized_username = self._normalize_required_text(
            username, "username", self.MAX_USERNAME_LENGTH
        )
        if not isinstance(authentication_type, AuthenticationType):
            raise InvalidConnection("Authentication type is invalid")
        if not isinstance(last_status, ConnectionStatus):
            raise InvalidConnection("Connection status is invalid")
        if (
            not isinstance(connection_timeout, int)
            or isinstance(connection_timeout, bool)
            or connection_timeout <= 0
        ):
            raise InvalidConnection("Connection timeout must be a positive integer")
        if not isinstance(is_default, bool):
            raise InvalidConnection("Default connection flag must be a boolean")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidConnection("Connection version must be a positive integer")
        if last_error is not None and not isinstance(last_error, str):
            raise InvalidConnection("Last error must be a string")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidConnection("Update time cannot precede connection creation")
        if last_connected_at is not None:
            self._validate_timestamp(last_connected_at, "last_connected_at")
            if last_connected_at < created_at:
                raise InvalidConnection(
                    "Last connected time cannot precede connection creation"
                )
            if last_connected_at > updated_at:
                raise InvalidConnection("Last connected time cannot follow the last update")

        super().__init__(entity_id)
        self._device_id = device_id
        self._name = normalized_name
        self._endpoint = endpoint
        self._username = normalized_username
        self._authentication_type = authentication_type
        self._connection_timeout = connection_timeout
        self._is_default = is_default
        self._last_connected_at = last_connected_at
        self._last_status = last_status
        self._last_error = last_error
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _normalize_required_text(value: str, name: str, max_length: int) -> str:
        if not isinstance(value, str):
            raise InvalidConnection(f"Connection {name} must be a string")
        normalized_value = value.strip()
        if not normalized_value or len(normalized_value) > max_length:
            raise InvalidConnection(f"Connection {name} is invalid")
        return normalized_value

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidConnection(f"Connection {name} must include a timezone")

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"connection-{self.id.hex[:8]}")

    @property
    def host(self) -> str:
        return self._endpoint.host

    @property
    def endpoint(self) -> ConnectionEndpoint:
        return self._endpoint

    @property
    def username(self) -> str:
        return self._username

    @property
    def authentication_type(self) -> AuthenticationType:
        return self._authentication_type

    @property
    def port(self) -> int:
        return self._endpoint.port

    @property
    def connection_timeout(self) -> int:
        return self._connection_timeout

    @property
    def is_default(self) -> bool:
        return self._is_default

    @property
    def last_connected_at(self) -> datetime | None:
        return self._last_connected_at

    @property
    def last_status(self) -> ConnectionStatus:
        return self._last_status

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
