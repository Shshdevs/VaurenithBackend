from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring.interfaces import MetricRepository
from app.domain.monitoring import Metric as MetricEntity
from app.infrastructure.persistence.models.monitoring.metric import Metric


class SqlAlchemyMetricRepository(MetricRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, metric: MetricEntity) -> None:
        self._session.add(
            Metric(
                id=metric.id,
                device_id=metric.device_id,
                metric_type=metric.metric_type,
                value=metric.value,
                unit=metric.unit,
                source=metric.source,
                collected_at=metric.collected_at,
            )
        )

    async def get_for_device(
        self,
        device_id: UUID,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[MetricEntity]:
        statement = select(Metric).where(Metric.device_id == device_id)
        if start is not None:
            statement = statement.where(Metric.collected_at >= start)
        if end is not None:
            statement = statement.where(Metric.collected_at < end)
        statement = statement.order_by(Metric.collected_at.desc(), Metric.id.desc())
        result = await self._session.execute(statement.limit(limit).offset(offset))
        return [self._to_entity(model) for model in result.scalars().all()]

    @staticmethod
    def _to_entity(model: Metric) -> MetricEntity:
        return MetricEntity(
            entity_id=model.id,
            device_id=model.device_id,
            metric_type=model.metric_type,
            value=model.value,
            unit=model.unit,
            source=model.source,
            collected_at=model.collected_at,
        )
