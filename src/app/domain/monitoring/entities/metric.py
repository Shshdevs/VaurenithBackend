from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ...common.entity import Entity
from ...common.types import EntityId
from ..enums import MetricType, MetricUnit
from ..exceptions import InvalidMetric
from ..value_objects import MetricValue


class Metric(Entity):
    """Time-series infrastructure metrics with limited retention"""

    MAX_SOURCE_LENGTH = 255

    def __init__(
        self,
        entity_id: EntityId,
        device_id: EntityId,
        metric_type: MetricType,
        value: MetricValue | Decimal,
        unit: MetricUnit,
        collected_at: datetime,
        source: str | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(device_id, UUID):
            raise InvalidMetric("Metric and device identifiers must be UUIDs")
        if not isinstance(metric_type, MetricType):
            raise InvalidMetric("Metric type is invalid")
        if not isinstance(unit, MetricUnit):
            raise InvalidMetric("Metric unit is invalid")
        metric_value = value if isinstance(value, MetricValue) else MetricValue(value)
        if source is not None and (
            not isinstance(source, str) or len(source) > self.MAX_SOURCE_LENGTH
        ):
            raise InvalidMetric("Metric source must be at most 255 characters")
        if not isinstance(collected_at, datetime) or collected_at.utcoffset() is None:
            raise InvalidMetric("Metric collection time must include a timezone")

        super().__init__(entity_id)
        self._device_id = device_id
        self._metric_type = metric_type
        self._value = metric_value
        self._unit = unit
        self._source = source
        self._collected_at = collected_at

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def metric_type(self) -> MetricType:
        return self._metric_type

    @property
    def value(self) -> Decimal:
        return self._value.value

    @property
    def metric_value(self) -> MetricValue:
        return self._value

    @property
    def unit(self) -> MetricUnit:
        return self._unit

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def collected_at(self) -> datetime:
        return self._collected_at
