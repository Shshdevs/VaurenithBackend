from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.enums import EntityType
from app.domain.monitoring import Event, EventResult, EventType


@dataclass(frozen=True, slots=True)
class EventData:
    id: UUID
    user_id: UUID
    project_id: UUID | None
    device_id: UUID | None
    event_type: EventType
    entity_type: EntityType | None
    entity_id: UUID | None
    description: str | None
    result: EventResult
    metadata: Any | None
    client_device_id: UUID | None
    created_at: datetime

    @classmethod
    def from_event(cls, event: Event) -> "EventData":
        return cls(
            id=event.id,
            user_id=event.user_id,
            project_id=event.project_id,
            device_id=event.device_id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            description=event.description,
            result=event.result,
            metadata=event.metadata,
            client_device_id=event.client_device_id,
            created_at=event.created_at,
        )
