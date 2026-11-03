from dataclasses import dataclass

from ...common.value_object import ValueObject
from ..exceptions import InvalidCodeComponent


@dataclass(frozen=True, slots=True, eq=False)
class ComponentPath(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCodeComponent("Component path must be a string")
        normalized_value = self.value.strip()
        if not normalized_value:
            raise InvalidCodeComponent("Component path is invalid")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
