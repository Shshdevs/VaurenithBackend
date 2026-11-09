from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.enums import ContainerStatus
from app.domain.infrastructure.exceptions import InvalidContainer
from app.domain.infrastructure.value_objects import (
    ContainerImage,
    ContainerName,
    ContainerRuntimeId,
)


class Container(Entity):
    """Container metadata obtained from Docker Engine or another supported runtime"""

    def __init__(
        self,
        entity_id: EntityId,
        device_id: EntityId,
        container_runtime_id: ContainerRuntimeId,
        name: ContainerName,
        created_at: datetime,
        updated_at: datetime,
        project_id: EntityId | None = None,
        environment_id: EntityId | None = None,
        service_id: EntityId | None = None,
        image: ContainerImage | None = None,
        status: ContainerStatus = ContainerStatus.UNKNOWN,
        ports: Any | None = None,
        volumes: Any | None = None,
        networks: Any | None = None,
        started_at: datetime | None = None,
        last_seen_at: datetime | None = None,
        metadata: Any | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(device_id, UUID):
            raise InvalidContainer("Container and device identifiers must be UUIDs")
        for identifier, field_name in (
            (project_id, "project"),
            (environment_id, "environment"),
            (service_id, "service"),
        ):
            if identifier is not None and not isinstance(identifier, UUID):
                raise InvalidContainer(
                    f"{field_name.capitalize()} identifier must be a UUID"
                )

        if not isinstance(container_runtime_id, ContainerRuntimeId):
            raise InvalidContainer("Container runtime ID must be a ContainerRuntimeId")
        if not isinstance(name, ContainerName):
            raise InvalidContainer("Container name must be a ContainerName")
        if image is not None and not isinstance(image, ContainerImage):
            raise InvalidContainer("Container image must be a ContainerImage")
        if not isinstance(status, ContainerStatus):
            raise InvalidContainer("Container status is invalid")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidContainer("Container version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidContainer("Update time cannot precede container creation")
        if started_at is not None:
            self._validate_timestamp(started_at, "started_at")
        if last_seen_at is not None:
            self._validate_timestamp(last_seen_at, "last_seen_at")
        if (
            started_at is not None
            and last_seen_at is not None
            and last_seen_at < started_at
        ):
            raise InvalidContainer("Last seen time cannot precede container start")

        super().__init__(entity_id)
        self._device_id = device_id
        self._project_id = project_id
        self._environment_id = environment_id
        self._service_id = service_id
        self._container_runtime_id = container_runtime_id
        self._name = name
        self._image = image
        self._status = status
        self._ports = deepcopy(ports)
        self._volumes = deepcopy(volumes)
        self._networks = deepcopy(networks)
        self._started_at = started_at
        self._last_seen_at = last_seen_at
        self._metadata = deepcopy(metadata)
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidContainer(f"Container {name} must include a timezone")

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
    def service_id(self) -> EntityId | None:
        return self._service_id

    @property
    def container_runtime_id(self) -> str:
        return self._container_runtime_id.value

    @property
    def container_runtime_id_value(self) -> ContainerRuntimeId:
        return self._container_runtime_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"container-{self.id.hex[:8]}")

    @property
    def name_value(self) -> ContainerName:
        return self._name

    @property
    def image(self) -> str | None:
        return self._image.value if self._image is not None else None

    @property
    def image_value(self) -> ContainerImage | None:
        return self._image

    @property
    def status(self) -> ContainerStatus:
        return self._status

    @property
    def ports(self) -> Any | None:
        return deepcopy(self._ports)

    @property
    def volumes(self) -> Any | None:
        return deepcopy(self._volumes)

    @property
    def networks(self) -> Any | None:
        return deepcopy(self._networks)

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def last_seen_at(self) -> datetime | None:
        return self._last_seen_at

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
