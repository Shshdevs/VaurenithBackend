from dataclasses import dataclass
from typing import ClassVar

from ...common.value_object import ValueObject
from ..exceptions import InvalidContainer


@dataclass(frozen=True, slots=True, eq=False)
class ContainerName(ValueObject):
    MAX_LENGTH: ClassVar[int] = 255
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidContainer("Container name must be a string")
        normalized_value = self.value.strip()
        if not normalized_value or len(normalized_value) > self.MAX_LENGTH:
            raise InvalidContainer("Container name is invalid")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
