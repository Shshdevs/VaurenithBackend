from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.monitoring import Event, EventResult, EventType


class EventRepository(Protocol):
    async def create(self, event: Event) -> None: ...

    async def owns_client_device(self, user_id: UUID, client_device_id: UUID) -> bool: ...

    async def get_user_events(
        self,
        user_id: UUID,
        project_id: UUID | None,
        device_id: UUID | None,
        event_type: EventType | None,
        result: EventResult | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[Event]: ...
