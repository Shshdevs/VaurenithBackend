from datetime import datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.monitoring.dto import EventData
from app.application.monitoring.interfaces import EventRepository
from app.domain.monitoring import EventResult, EventType


class GetUserEvents:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    async def get_user_events(
        self,
        identity: VerifiedIdentity,
        project_id: UUID | None,
        device_id: UUID | None,
        event_type: EventType | None,
        result: EventResult | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[EventData]:
        if any(
            boundary is not None
            and (boundary.tzinfo is None or boundary.utcoffset() is None)
            for boundary in (start, end)
        ):
            raise InvalidInput("Event range boundaries must include a timezone")
        if start is not None and end is not None and start >= end:
            raise InvalidInput("Event range start must precede end")
        events = await self._event_repository.get_user_events(
            user_id=identity.user_id,
            project_id=project_id,
            device_id=device_id,
            event_type=event_type,
            result=result,
            start=start,
            end=end,
            limit=limit,
            offset=offset,
        )
        return [EventData.from_event(event) for event in events]
