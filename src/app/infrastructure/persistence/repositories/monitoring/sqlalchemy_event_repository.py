from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring.interfaces import EventRepository
from app.domain.monitoring import Event as EventEntity
from app.domain.monitoring import EventResult, EventType
from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.monitoring.event import Event


class SqlAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, event: EventEntity) -> None:
        self._session.add(
            Event(
                id=event.id,
                user_id=event.user_id,
                project_id=event.project_id,
                device_id=event.device_id,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                description=event.description,
                result=event.result,
                metadata_=event.metadata,
                client_device_id=event.client_device_id,
                created_at=event.created_at,
            )
        )

    async def owns_client_device(self, user_id: UUID, client_device_id: UUID) -> bool:
        result = await self._session.execute(
            select(ClientDevice.id).where(
                ClientDevice.id == client_device_id,
                ClientDevice.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

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
    ) -> list[EventEntity]:
        statement = select(Event).where(Event.user_id == user_id)
        if project_id is not None:
            statement = statement.where(Event.project_id == project_id)
        if device_id is not None:
            statement = statement.where(Event.device_id == device_id)
        if event_type is not None:
            statement = statement.where(Event.event_type == event_type)
        if result is not None:
            statement = statement.where(Event.result == result)
        if start is not None:
            statement = statement.where(Event.created_at >= start)
        if end is not None:
            statement = statement.where(Event.created_at < end)
        statement = statement.order_by(Event.created_at.desc(), Event.id.desc())
        result_set = await self._session.execute(statement.limit(limit).offset(offset))
        return [self._to_entity(model) for model in result_set.scalars().all()]

    @staticmethod
    def _to_entity(model: Event) -> EventEntity:
        return EventEntity(
            event_id=model.id,
            user_id=model.user_id,
            event_type=model.event_type,
            result=model.result,
            created_at=model.created_at,
            project_id=model.project_id,
            device_id=model.device_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            description=model.description,
            metadata=model.metadata_,
            client_device_id=model.client_device_id,
        )
