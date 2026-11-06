from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.identity.exceptions import InvalidTokenHash


@dataclass(frozen=True, slots=True, eq=False)
class TokenHash(ValueObject):
    MAX_LENGTH: ClassVar[int] = 512
    value: str

    def __post_init__(self) -> None:
        if (
            not self.value
            or len(self.value) > self.MAX_LENGTH
            or any(character.isspace() for character in self.value)
        ):
            raise InvalidTokenHash("Token hash is invalid")

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
