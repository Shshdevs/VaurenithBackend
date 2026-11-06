from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.development.exceptions import InvalidBranch


@dataclass(frozen=True, slots=True, eq=False)
class BranchName(ValueObject):
    MAX_LENGTH: ClassVar[int] = 255
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidBranch("Branch name must be a string")
        if not self.value or len(self.value) > self.MAX_LENGTH:
            raise InvalidBranch("Branch name is invalid")
        if not self._is_valid_branch_name(self.value):
            raise InvalidBranch("Branch name is not a valid Git branch name")

    @staticmethod
    def _is_valid_branch_name(value: str) -> bool:
        if (
            value.startswith("-")
            or value.startswith("/")
            or value.endswith("/")
            or value.endswith(".")
            or value == "@"
            or "//" in value
            or ".." in value
            or "@{" in value
        ):
            return False
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            return False
        if any(character in " ~^:?*[\\" for character in value):
            return False
        return all(
            not component.startswith(".") and not component.endswith(".lock")
            for component in value.split("/")
        )

    def equality_components(self) -> tuple[str, ...]:
        return (self.value,)

    def __str__(self) -> str:
        return self.value
