from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.identity.exceptions import InvalidEmail


@dataclass(frozen=True, slots=True, eq=False)
class EmailAddress(ValueObject):
    MAX_LENGTH: ClassVar[int] = 320
    value: str

    def __post_init__(self) -> None:
        normalized_value = self.value.strip()
        local_part, separator, domain = normalized_value.partition("@")
        if (
            not separator
            or not local_part
            or not domain
            or "@" in domain
            or any(character.isspace() for character in normalized_value)
            or len(normalized_value) > self.MAX_LENGTH
        ):
            raise InvalidEmail("Email address is invalid")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
