from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from ...common.entity import Entity
from ...common.types import EntityId
from ..enums import DbmsType, ResourceStatus
from ..exceptions import InvalidDatabase
from ..value_objects import (
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
        name: str,
        dbms_type: DbmsType,
        created_at: datetime,
        updated_at: datetime,
        project_id: EntityId | None = None,
        environment_id: EntityId | None = None,
        container_id: EntityId | None = None,
        service_id: EntityId | None = None,
        host: str | None = None,
        port: int | None = None,
        database_name: str | None = None,
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

        resource_name = DatabaseResourceName(name)
        endpoint = None
        if host is not None or port is not None:
            endpoint_value = DatabaseEndpoint(host=host, port=port)
            if endpoint_value.host is not None or endpoint_value.port is not None:
                endpoint = endpoint_value
        catalog_name = None
        if database_name is not None and not (
            isinstance(database_name, str) and not database_name.strip()
        ):
            catalog_name = DatabaseCatalogName(database_name)
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
        self._name = resource_name
        self._dbms_type = dbms_type
        self._endpoint = endpoint
        self._database_name = catalog_name
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
