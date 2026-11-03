from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.domain.monitoring.entities.metric import Metric
from app.domain.monitoring.enums import MetricType, MetricUnit
from app.domain.monitoring.exceptions import InvalidMetric
from app.domain.monitoring.value_objects import MetricValue


def make_metric(**overrides: Any) -> Metric:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "device_id": uuid4(),
        "metric_type": MetricType.CPU_USAGE,
        "value": Decimal("42.125000"),
        "unit": MetricUnit.PERCENT,
        "collected_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return Metric(**values)


def test_metric_exposes_normalized_numeric_value() -> None:
    metric = make_metric()

    assert metric.metric_type is MetricType.CPU_USAGE
    assert metric.value == Decimal("42.125000")
    assert metric.metric_value == MetricValue(Decimal("42.125000"))
    assert metric.unit is MetricUnit.PERCENT


@pytest.mark.parametrize(
    "value",
    [Decimal("-0.000001"), Decimal("0.0000001"), Decimal("100000000000000")],
)
def test_metric_rejects_values_not_representable_by_column(value: Decimal) -> None:
    with pytest.raises(InvalidMetric):
        make_metric(value=value)


def test_metric_rejects_invalid_source_and_naive_timestamp() -> None:
    with pytest.raises(InvalidMetric):
        make_metric(source="x" * 256)
    with pytest.raises(InvalidMetric):
        make_metric(collected_at=datetime(2026, 1, 1))
