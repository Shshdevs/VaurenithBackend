from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.common.enums import EntityType
from app.domain.monitoring import EventResult, EventType


class EventData(Schema):
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


class EventCreateRequest(Schema):
    event_type: EventType
    result: EventResult
    created_at: datetime
    project_id: UUID | None = None
    device_id: UUID | None = None
    description: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, Any] | None = None
    client_device_id: UUID | None = None
