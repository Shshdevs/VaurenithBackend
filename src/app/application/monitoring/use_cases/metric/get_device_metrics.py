from datetime import datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.monitoring.dto import MetricData
from app.application.monitoring.interfaces import MetricRepository


class GetDeviceMetrics:
    def __init__(
        self,
        metric_repository: MetricRepository,
        device_repository: DeviceRepository,
    ) -> None:
        self._metric_repository = metric_repository
        self._device_repository = device_repository

    async def get_device_metrics(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[MetricData]:
        device = await self._device_repository.get_by_id(identity, device_id)
        if device is None:
            raise DeviceNotFound(str(device_id))
        if any(
            boundary is not None
            and (boundary.tzinfo is None or boundary.utcoffset() is None)
            for boundary in (start, end)
        ):
            raise InvalidInput("Metric range boundaries must include a timezone")
        if start is not None and end is not None and start >= end:
            raise InvalidInput("Metric range start must precede end")
        metrics = await self._metric_repository.get_for_device(
            device_id, start, end, limit, offset
        )
        return [MetricData.from_metric(metric) for metric in metrics]
