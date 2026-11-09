from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.enums import DbmsType, ResourceStatus
from app.domain.infrastructure.exceptions import InvalidDatabase
from app.domain.infrastructure.value_objects import (
    DatabaseCatalogName,
    DatabaseEndpoint,
    DatabaseResourceName,
)


class Database(Entity):
    """Metadata about externally managed databases.
    Database credentials are never stored here."""

    def __init__(
        self,
        entity_id: EntityId,
        device_id: EntityId,
        name: DatabaseResourceName,
        dbms_type: DbmsType,
        created_at: datetime,
        updated_at: datetime,
        project_id: EntityId | None = None,
        environment_id: EntityId | None = None,
        container_id: EntityId | None = None,
        service_id: EntityId | None = None,
        endpoint: DatabaseEndpoint | None = None,
        database_name: DatabaseCatalogName | None = None,
        status: ResourceStatus = ResourceStatus.UNKNOWN,
        last_checked_at: datetime | None = None,
        metadata: Any | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(device_id, UUID):
            raise InvalidDatabase("Database and device identifiers must be UUIDs")
        for identifier, field_name in (
            (project_id, "project"),
            (environment_id, "environment"),
            (container_id, "container"),
            (service_id, "service"),
        ):
            if identifier is not None and not isinstance(identifier, UUID):
                raise InvalidDatabase(
                    f"{field_name.capitalize()} identifier must be a UUID"
                )

        if not isinstance(name, DatabaseResourceName):
            raise InvalidDatabase("Database resource name must be a DatabaseResourceName")
        if endpoint is not None and not isinstance(endpoint, DatabaseEndpoint):
            raise InvalidDatabase("Database endpoint must be a DatabaseEndpoint")
        if endpoint is not None and endpoint.host is None and endpoint.port is None:
            endpoint = None
        if database_name is not None and not isinstance(database_name, DatabaseCatalogName):
            raise InvalidDatabase("Database name must be a DatabaseCatalogName")
        if not isinstance(dbms_type, DbmsType):
            raise InvalidDatabase("Database management system type is invalid")
        if not isinstance(status, ResourceStatus):
            raise InvalidDatabase("Database status is invalid")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidDatabase("Database version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidDatabase("Update time cannot precede database creation")
        if last_checked_at is not None:
            self._validate_timestamp(last_checked_at, "last_checked_at")
            if last_checked_at < created_at:
                raise InvalidDatabase("Check time cannot precede database creation")
            if last_checked_at > updated_at:
                raise InvalidDatabase("Check time cannot follow the last update")

        super().__init__(entity_id)
        self._device_id = device_id
        self._project_id = project_id
        self._environment_id = environment_id
        self._container_id = container_id
        self._service_id = service_id
        self._name = name
        self._dbms_type = dbms_type
        self._endpoint = endpoint
        self._database_name = database_name
        self._status = status
        self._last_checked_at = last_checked_at
        self._metadata = deepcopy(metadata)
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidDatabase(f"Database {name} must include a timezone")

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def project_id(self) -> EntityId | None:
        return self._project_id

    @property
    def environment_id(self) -> EntityId | None:
        return self._environment_id

    @property
    def container_id(self) -> EntityId | None:
        return self._container_id

    @property
    def service_id(self) -> EntityId | None:
        return self._service_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"database-{self.id.hex[:8]}")

    @property
    def name_value(self) -> DatabaseResourceName:
        return self._name

    @property
    def dbms_type(self) -> DbmsType:
        return self._dbms_type

    @property
    def endpoint(self) -> DatabaseEndpoint | None:
        return self._endpoint

    @property
    def host(self) -> str | None:
        return self._endpoint.host if self._endpoint is not None else None

    @property
    def port(self) -> int | None:
        return self._endpoint.port if self._endpoint is not None else None

    @property
    def database_name(self) -> str | None:
        return self._database_name.value if self._database_name is not None else None

    @property
    def database_name_value(self) -> DatabaseCatalogName | None:
        return self._database_name

    @property
    def status(self) -> ResourceStatus:
        return self._status

    @property
    def last_checked_at(self) -> datetime | None:
        return self._last_checked_at

    @property
    def metadata(self) -> Any | None:
        return deepcopy(self._metadata)

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
