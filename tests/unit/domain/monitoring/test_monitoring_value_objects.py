from decimal import Decimal

import pytest

from app.domain.monitoring.exceptions import InvalidMetric
from app.domain.monitoring.value_objects import MetricValue


def test_metric_value_normalizes_scale() -> None:
    assert MetricValue(Decimal("1.2500000")).value == Decimal("1.250000")


@pytest.mark.parametrize("value", [Decimal("-0.1"), Decimal("NaN"), Decimal("Infinity")])
def test_metric_value_rejects_invalid_values(value: Decimal) -> None:
    with pytest.raises(InvalidMetric):
        MetricValue(value)
