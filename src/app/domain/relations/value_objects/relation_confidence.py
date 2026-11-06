from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.relations.exceptions import InvalidRelation


@dataclass(frozen=True, slots=True, eq=False)
class RelationConfidence(ValueObject):
    SCALE: ClassVar[Decimal] = Decimal("0.0001")
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvalidRelation("Relation confidence must be a Decimal")
        if not self.value.is_finite() or not Decimal("0") <= self.value <= Decimal("1"):
            raise InvalidRelation("Relation confidence must be between 0 and 1")
        normalized_value = self.value.quantize(self.SCALE)
        if normalized_value != self.value:
            raise InvalidRelation(
                "Relation confidence can have at most 4 decimal places"
            )
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[Decimal, ...]:
        return (self.value,)
