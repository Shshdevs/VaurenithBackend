from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.enums import EntityType
from app.domain.common.types import EntityId
from app.domain.monitoring.enums import EventResult, EventType
from app.domain.monitoring.exceptions import InvalidEvent


class Event(Entity):
    """Unified event timeline. Secrets must never be included"""

    def __init__(
        self,
        event_id: EntityId,
        user_id: EntityId,
        event_type: EventType,
        result: EventResult,
        created_at: datetime,
        project_id: EntityId | None = None,
        device_id: EntityId | None = None,
        entity_type: EntityType | None = None,
        entity_id: EntityId | None = None,
        description: str | None = None,
        metadata: Any | None = None,
        client_device_id: EntityId | None = None,
    ) -> None:
        for identifier, name in (
            (event_id, "event"),
            (user_id, "user"),
        ):
            if not isinstance(identifier, UUID):
                raise InvalidEvent(f"{name.capitalize()} identifier must be a UUID")
        for identifier, name in (
            (project_id, "project"),
            (device_id, "device"),
            (entity_id, "related entity"),
            (client_device_id, "client device"),
        ):
            if identifier is not None and not isinstance(identifier, UUID):
                raise InvalidEvent(f"{name.capitalize()} identifier must be a UUID")
        if not isinstance(event_type, EventType):
            raise InvalidEvent("Event type is invalid")
        if entity_type is not None and not isinstance(entity_type, EntityType):
            raise InvalidEvent("Entity type is invalid")
        if not isinstance(result, EventResult):
            raise InvalidEvent("Event result is invalid")
        if description is not None and not isinstance(description, str):
            raise InvalidEvent("Event description must be a string")
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidEvent("Event creation time must include a timezone")

        super().__init__(event_id)
        self._user_id = user_id
        self._project_id = project_id
        self._device_id = device_id
        self._event_type = event_type
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._description = description
        self._result = result
        self._metadata = deepcopy(metadata)
        self._client_device_id = client_device_id
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
    def event_type(self) -> EventType:
        return self._event_type

    @property
    def entity_type(self) -> EntityType | None:
        return self._entity_type

    @property
    def entity_id(self) -> EntityId | None:
        return self._entity_id

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def result(self) -> EventResult:
        return self._result

    @property
    def metadata(self) -> Any | None:
        return deepcopy(self._metadata)

    @property
    def client_device_id(self) -> EntityId | None:
        return self._client_device_id

    @property
    def created_at(self) -> datetime:
        return self._created_at
