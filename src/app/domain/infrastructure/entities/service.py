from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.enums import ResourceStatus, ServiceType
from app.domain.infrastructure.exceptions import InvalidService
from app.domain.infrastructure.value_objects import ServiceName, SystemIdentifier


class Service(Entity):
    def __init__(
        self,
        entity_id: EntityId,
        device_id: EntityId,
        name: str,
        service_type: ServiceType,
        created_at: datetime,
        updated_at: datetime,
        project_id: EntityId | None = None,
        environment_id: EntityId | None = None,
        description: str | None = None,
        system_identifier: str | None = None,
        status: ResourceStatus = ResourceStatus.UNKNOWN,
        last_status_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(device_id, UUID):
            raise InvalidService("Service and device identifiers must be UUIDs")
        if project_id is not None and not isinstance(project_id, UUID):
            raise InvalidService("Project identifier must be a UUID")
        if environment_id is not None and not isinstance(environment_id, UUID):
            raise InvalidService("Environment identifier must be a UUID")

        service_name = ServiceName(name)
        normalized_system_identifier = None
        if system_identifier is not None and not (
            isinstance(system_identifier, str) and not system_identifier.strip()
        ):
            normalized_system_identifier = SystemIdentifier(system_identifier)
        if description is not None and not isinstance(description, str):
            raise InvalidService("Service description must be a string")
        if not isinstance(service_type, ServiceType):
            raise InvalidService("Service type is invalid")
        if not isinstance(status, ResourceStatus):
            raise InvalidService("Service status is invalid")
        if metadata is not None and not isinstance(metadata, dict):
            raise InvalidService("Service metadata must be a JSON object")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidService("Service version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidService("Update time cannot precede service creation")
        if last_status_at is not None:
            self._validate_timestamp(last_status_at, "last_status_at")
            if last_status_at < created_at:
                raise InvalidService("Status time cannot precede service creation")
            if last_status_at > updated_at:
                raise InvalidService("Status time cannot follow the last update")

        super().__init__(entity_id)
        self._device_id = device_id
        self._project_id = project_id
        self._environment_id = environment_id
        self._name = service_name
        self._service_type = service_type
        self._description = description
        self._system_identifier = normalized_system_identifier
        self._status = status
        self._last_status_at = last_status_at
        self._metadata = deepcopy(metadata)
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidService(f"Service {name} must include a timezone")

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
    def name(self) -> str:
        return self._name.value

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"service-{self.id.hex[:8]}")

    @property
    def name_value(self) -> ServiceName:
        return self._name

    @property
    def service_type(self) -> ServiceType:
        return self._service_type

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def system_identifier(self) -> str | None:
        return (
            self._system_identifier.value
            if self._system_identifier is not None
            else None
        )

    @property
    def system_identifier_value(self) -> SystemIdentifier | None:
        return self._system_identifier

    @property
    def status(self) -> ResourceStatus:
        return self._status

    @property
    def last_status_at(self) -> datetime | None:
        return self._last_status_at

    @property
    def metadata(self) -> dict[str, Any] | None:
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
