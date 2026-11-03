from dataclasses import dataclass
from typing import ClassVar

from ...common.value_object import ValueObject
from ..exceptions import InvalidService


@dataclass(frozen=True, slots=True, eq=False)
class ServiceName(ValueObject):
    MAX_LENGTH: ClassVar[int] = 255
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidService("Service name must be a string")
        normalized_value = self.value.strip()
        if not normalized_value or len(normalized_value) > self.MAX_LENGTH:
            raise InvalidService("Service name is invalid")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
