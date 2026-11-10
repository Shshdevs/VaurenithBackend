from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.exceptions import ChangeLogCursorExpired
from app.domain.synchronization import ChangeLog
from app.infrastructure.persistence.models.synchronization import (
    ChangeLog as ChangeLogModel,
)
from app.infrastructure.persistence.models.synchronization import (
    ChangeLogRetention,
)

CHANGE_LOG_RETENTION = timedelta(days=365)


class SqlAlchemyChangeLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, change: ChangeLog) -> None:
        await self._lock_user(change.user_id)
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
        await self._lock_user(user_id)
        cutoff = datetime.now(UTC) - CHANGE_LOG_RETENTION
        recorded_expired_sequence = await self._session.scalar(
            select(ChangeLogRetention.expired_through_sequence).where(
                ChangeLogRetention.user_id == user_id
            )
        )
        unpurged_expired_sequence = await self._session.scalar(
            select(func.max(ChangeLogModel.sequence)).where(
                ChangeLogModel.user_id == user_id,
                ChangeLogModel.created_at < cutoff,
            )
        )
        expired_through_sequence = max(
            recorded_expired_sequence or 0,
            unpurged_expired_sequence or 0,
        )
        if after_sequence < expired_through_sequence:
            latest_sequence = await self._session.scalar(
                select(func.max(ChangeLogModel.sequence)).where(
                    ChangeLogModel.user_id == user_id
                )
            )
            raise ChangeLogCursorExpired(
                max(expired_through_sequence, latest_sequence or 0)
            )
        statement = (
            select(ChangeLogModel)
            .where(
                ChangeLogModel.user_id == user_id,
                ChangeLogModel.sequence > after_sequence,
                ChangeLogModel.created_at >= cutoff,
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

    async def purge_expired(self, cutoff: datetime) -> int:
        user_ids = list(
            await self._session.scalars(
                select(ChangeLogModel.user_id)
                .where(ChangeLogModel.created_at < cutoff)
                .distinct()
                .order_by(ChangeLogModel.user_id)
            )
        )
        deleted_count = 0
        for user_id in user_ids:
            await self._lock_user(user_id)
            deleted_count += await self._purge_expired_for_user(user_id, cutoff)
        return deleted_count

    async def _purge_expired_for_user(self, user_id: UUID, cutoff: datetime) -> int:
        expired_through_sequence = await self._session.scalar(
            select(func.max(ChangeLogModel.sequence)).where(
                ChangeLogModel.user_id == user_id,
                ChangeLogModel.created_at < cutoff,
            )
        )
        if expired_through_sequence is None:
            return 0

        retention_insert = insert(ChangeLogRetention).values(
            user_id=user_id,
            expired_through_sequence=expired_through_sequence,
        )
        await self._session.execute(
            retention_insert.on_conflict_do_update(
                index_elements=[ChangeLogRetention.user_id],
                set_={
                    "expired_through_sequence": func.greatest(
                        ChangeLogRetention.expired_through_sequence,
                        retention_insert.excluded.expired_through_sequence,
                    ),
                    "updated_at": func.now(),
                },
            )
        )
        deleted_ids = await self._session.scalars(
            delete(ChangeLogModel)
            .where(
                ChangeLogModel.user_id == user_id,
                ChangeLogModel.created_at < cutoff,
            )
            .returning(ChangeLogModel.id)
        )
        return len(deleted_ids.all())

    async def _lock_user(self, user_id: UUID) -> None:
        await self._session.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:user_id AS text), 0))"
            ),
            {"user_id": str(user_id)},
        )
