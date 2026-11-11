from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.monitoring import Metric


class MetricRepository(Protocol):
    async def create(self, metric: Metric) -> None: ...

    async def get_for_device(
        self,
        device_id: UUID,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[Metric]: ...
