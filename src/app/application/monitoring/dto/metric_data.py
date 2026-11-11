from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.monitoring import Metric, MetricType, MetricUnit


@dataclass(frozen=True, slots=True)
class MetricData:
    id: UUID
    device_id: UUID
    metric_type: MetricType
    value: Decimal
    unit: MetricUnit
    source: str | None
    collected_at: datetime

    @classmethod
    def from_metric(cls, metric: Metric) -> "MetricData":
        return cls(
            id=metric.id,
            device_id=metric.device_id,
            metric_type=metric.metric_type,
            value=metric.value,
            unit=metric.unit,
            source=metric.source,
            collected_at=metric.collected_at,
        )
