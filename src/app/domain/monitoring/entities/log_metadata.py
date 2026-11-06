from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.monitoring.exceptions import InvalidLogMetadata


class LogMetadata(Entity):
    """Cloud-safe log metadata and references. Raw logs remain local by default."""

    MAX_SOURCE_LENGTH = 255
    MAX_SEVERITY_LENGTH = 50
    MIN_RECORDS_COUNT = -(2**63)
    MAX_RECORDS_COUNT = 2**63 - 1

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        source: str,
        created_at: datetime,
        project_id: EntityId | None = None,
        device_id: EntityId | None = None,
        service_id: EntityId | None = None,
        container_id: EntityId | None = None,
        reference: str | None = None,
        description: str | None = None,
        severity: str | None = None,
        records_count: int | None = None,
        collected_at: datetime | None = None,
    ) -> None:
        for identifier, name in (
            (entity_id, "log metadata"),
            (user_id, "user"),
        ):
            if not isinstance(identifier, UUID):
                raise InvalidLogMetadata(
                    f"{name.capitalize()} identifier must be a UUID"
                )
        for identifier, name in (
            (project_id, "project"),
            (device_id, "device"),
            (service_id, "service"),
            (container_id, "container"),
        ):
            if identifier is not None and not isinstance(identifier, UUID):
                raise InvalidLogMetadata(
                    f"{name.capitalize()} identifier must be a UUID"
                )
        if not isinstance(source, str) or len(source) > self.MAX_SOURCE_LENGTH:
            raise InvalidLogMetadata("Log source must be a string of at most 255 chars")
        if reference is not None and not isinstance(reference, str):
            raise InvalidLogMetadata("Log reference must be a string")
        if description is not None and not isinstance(description, str):
            raise InvalidLogMetadata("Log description must be a string")
        if severity is not None and (
            not isinstance(severity, str) or len(severity) > self.MAX_SEVERITY_LENGTH
        ):
            raise InvalidLogMetadata("Log severity must be at most 50 characters")
        if records_count is not None and (
            not isinstance(records_count, int)
            or isinstance(records_count, bool)
            or not self.MIN_RECORDS_COUNT <= records_count <= self.MAX_RECORDS_COUNT
        ):
            raise InvalidLogMetadata("Log records count must fit in a 64-bit integer")
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidLogMetadata("Log creation time must include a timezone")
        if collected_at is not None and (
            not isinstance(collected_at, datetime) or collected_at.utcoffset() is None
        ):
            raise InvalidLogMetadata("Log collection time must include a timezone")

        super().__init__(entity_id)
        self._user_id = user_id
        self._project_id = project_id
        self._device_id = device_id
        self._service_id = service_id
        self._container_id = container_id
        self._source = source
        self._reference = reference
        self._description = description
        self._severity = severity
        self._records_count = records_count
        self._collected_at = collected_at
        self._created_at = created_at

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def project_id(self) -> EntityId | None:
        return self._project_id

    @property
    def device_id(self) -> EntityId | None:
        return self._device_id

    @property
    def service_id(self) -> EntityId | None:
        return self._service_id

    @property
    def container_id(self) -> EntityId | None:
        return self._container_id

    @property
    def source(self) -> str:
        return self._source

    @property
    def reference(self) -> str | None:
        return self._reference

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def severity(self) -> str | None:
        return self._severity

    @property
    def records_count(self) -> int | None:
        return self._records_count

    @property
    def collected_at(self) -> datetime | None:
        return self._collected_at

    @property
    def created_at(self) -> datetime:
        return self._created_at
