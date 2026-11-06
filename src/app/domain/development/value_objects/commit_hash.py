import re
from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.development.exceptions import InvalidCommitHash


@dataclass(frozen=True, slots=True, eq=False)
class CommitHash(ValueObject):
    SHA1_LENGTH: ClassVar[int] = 40
    SHA256_LENGTH: ClassVar[int] = 64
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCommitHash("Commit hash must be a string")
        normalized_value = self.value.strip().lower()
        if (
            len(normalized_value) not in (self.SHA1_LENGTH, self.SHA256_LENGTH)
            or re.fullmatch(r"[0-9a-f]+", normalized_value) is None
        ):
            raise InvalidCommitHash("Commit hash must be a SHA-1 or SHA-256 object ID")
        object.__setattr__(self, "value", normalized_value)

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
