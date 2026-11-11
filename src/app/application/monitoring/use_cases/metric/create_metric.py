from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.monitoring.dto import MetricData
from app.application.monitoring.interfaces import MetricRepository
from app.domain.monitoring import InvalidMetric, Metric, MetricType, MetricUnit


class CreateMetric:
    def __init__(
        self,
        metric_repository: MetricRepository,
        device_repository: DeviceRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._metric_repository = metric_repository
        self._device_repository = device_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_metric(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        metric_type: MetricType,
        value: Decimal,
        unit: MetricUnit,
        collected_at: datetime,
        source: str | None,
    ) -> MetricData:
        device = await self._device_repository.get_by_id(identity, device_id)
        if device is None:
            raise DeviceNotFound(str(device_id))
        try:
            metric = Metric(
                entity_id=uuid4(),
                device_id=device_id,
                metric_type=MetricType(metric_type),
                value=value,
                unit=MetricUnit(unit),
                collected_at=collected_at,
                source=source,
            )
        except (InvalidMetric, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._metric_repository.create(metric)
        return MetricData.from_metric(metric)
