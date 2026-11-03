from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from ...common.value_object import ValueObject
from ..exceptions import InvalidMetric


@dataclass(frozen=True, slots=True, eq=False)
class MetricValue(ValueObject):
    SCALE: ClassVar[Decimal] = Decimal("0.000001")
    MAX_VALUE: ClassVar[Decimal] = Decimal("99999999999999.999999")
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise InvalidMetric("Metric value must be a finite Decimal")
        if not Decimal("0") <= self.value <= self.MAX_VALUE:
            raise InvalidMetric("Metric value is outside the supported range")
        normalized_value = self.value.quantize(self.SCALE)
        if normalized_value != self.value:
            raise InvalidMetric("Metric value can have at most 6 decimal places")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[Decimal, ...]:
        return (self.value,)
