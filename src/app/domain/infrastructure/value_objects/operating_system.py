from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.infrastructure.exceptions import InvalidDevice


@dataclass(frozen=True, slots=True, eq=False)
class OperatingSystem(ValueObject):
    MAX_NAME_LENGTH: ClassVar[int] = 100
    MAX_VERSION_LENGTH: ClassVar[int] = 100
    MAX_ARCHITECTURE_LENGTH: ClassVar[int] = 50
    name: str | None
    version: str | None
    architecture: str | None

    def __post_init__(self) -> None:
        normalized_name = self._normalize_optional_text(
            self.name, "operating_system", self.MAX_NAME_LENGTH
        )
        normalized_version = self._normalize_optional_text(
            self.version, "os_version", self.MAX_VERSION_LENGTH
        )
        normalized_architecture = self._normalize_optional_text(
            self.architecture, "architecture", self.MAX_ARCHITECTURE_LENGTH
        )
        if (
            normalized_name is None
            and normalized_version is None
            and normalized_architecture is None
        ):
            raise InvalidDevice("At least one operating system field must be provided")
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "version", normalized_version)
        object.__setattr__(self, "architecture", normalized_architecture)

    @staticmethod
    def _normalize_optional_text(
        value: str | None, name: str, max_length: int
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDevice(f"Device {name} must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if len(normalized_value) > max_length:
            raise InvalidDevice(f"Device {name} is too long")
        return normalized_value

    def equality_components(self) -> tuple[str | None, ...]:
        return (self.name, self.version, self.architecture)
