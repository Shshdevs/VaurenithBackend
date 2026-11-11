from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring.interfaces import LogMetadataRepository
from app.domain.monitoring import LogMetadata as LogMetadataEntity
from app.infrastructure.persistence.models.monitoring.logs_metadata import LogsMetadata


class SqlAlchemyLogMetadataRepository(LogMetadataRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, value: LogMetadataEntity) -> None:
        self._session.add(
            LogsMetadata(
                id=value.id,
                user_id=value.user_id,
                project_id=value.project_id,
                device_id=value.device_id,
                service_id=value.service_id,
                container_id=value.container_id,
                source=value.source,
                reference=value.reference,
                description=value.description,
                severity=value.severity,
                records_count=value.records_count,
                collected_at=value.collected_at,
                created_at=value.created_at,
            )
        )

    async def get_user_log_metadata(
        self,
        user_id: UUID,
        project_id: UUID | None,
        device_id: UUID | None,
        service_id: UUID | None,
        container_id: UUID | None,
        source: str | None,
        severity: str | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[LogMetadataEntity]:
        statement = select(LogsMetadata).where(LogsMetadata.user_id == user_id)
        filters = (
            (LogsMetadata.project_id, project_id),
            (LogsMetadata.device_id, device_id),
            (LogsMetadata.service_id, service_id),
            (LogsMetadata.container_id, container_id),
            (LogsMetadata.source, source),
            (LogsMetadata.severity, severity),
        )
        for column, value in filters:
            if value is not None:
                statement = statement.where(column == value)
        if start is not None:
            statement = statement.where(LogsMetadata.collected_at >= start)
        if end is not None:
            statement = statement.where(LogsMetadata.collected_at < end)
        statement = statement.order_by(
            LogsMetadata.collected_at.desc().nullslast(),
            LogsMetadata.created_at.desc(),
            LogsMetadata.id.desc(),
        )
        result = await self._session.execute(statement.limit(limit).offset(offset))
        return [self._to_entity(model) for model in result.scalars().all()]

    @staticmethod
    def _to_entity(model: LogsMetadata) -> LogMetadataEntity:
        return LogMetadataEntity(
            entity_id=model.id,
            user_id=model.user_id,
            source=model.source,
            created_at=model.created_at,
            project_id=model.project_id,
            device_id=model.device_id,
            service_id=model.service_id,
            container_id=model.container_id,
            reference=model.reference,
            description=model.description,
            severity=model.severity,
            records_count=model.records_count,
            collected_at=model.collected_at,
        )
