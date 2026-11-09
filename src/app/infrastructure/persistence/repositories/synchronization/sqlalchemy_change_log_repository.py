from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.synchronization import ChangeLog
from app.infrastructure.persistence.models.synchronization import (
    ChangeLog as ChangeLogModel,
)


class SqlAlchemyChangeLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, change: ChangeLog) -> None:
        await self._session.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:user_id AS text), 0))"
            ),
            {"user_id": str(change.user_id)},
        )
        self._session.add(
            ChangeLogModel(
                id=change.id,
                user_id=change.user_id,
                entity_type=change.entity_type,
                entity_id=change.entity_id,
                operation=change.operation,
                version=change.version,
                changed_by_client_id=change.changed_by_client_id,
                changed_by_user_id=change.changed_by_user_id,
                payload=change.payload,
                created_at=change.created_at,
            )
        )
        await self._session.flush()

    async def get_by_user(
        self, user_id: UUID, after_sequence: int = 0, limit: int = 100
    ) -> list[ChangeLog]:
        statement = (
            select(ChangeLogModel)
            .where(
                ChangeLogModel.user_id == user_id,
                ChangeLogModel.sequence > after_sequence,
            )
            .order_by(ChangeLogModel.sequence)
            .limit(limit)
        )
        models = (await self._session.scalars(statement)).all()
        return [
            ChangeLog(
                change_log_id=model.id,
                user_id=model.user_id,
                entity_type=model.entity_type,
                entity_id=model.entity_id,
                operation=model.operation,
                version=model.version,
                changed_by_user_id=model.changed_by_user_id,
                changed_by_client_id=model.changed_by_client_id,
                payload=model.payload,
                created_at=model.created_at,
                sequence=model.sequence,
            )
            for model in models
        ]
