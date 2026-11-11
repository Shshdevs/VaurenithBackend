from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.monitoring import MetricType, MetricUnit


class MetricData(Schema):
    id: UUID
    device_id: UUID
    metric_type: MetricType
    value: Decimal
    unit: MetricUnit
    source: str | None
    collected_at: datetime


class MetricCreateRequest(Schema):
    metric_type: MetricType
    value: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    unit: MetricUnit
    collected_at: datetime
    source: str | None = Field(default=None, max_length=255)
