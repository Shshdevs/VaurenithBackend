from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.infrastructure.exceptions import InvalidDatabase


@dataclass(frozen=True, slots=True, eq=False)
class DatabaseEndpoint(ValueObject):
    MAX_HOST_LENGTH: ClassVar[int] = 512
    host: str | None
    port: int | None

    def __post_init__(self) -> None:
        normalized_host = self.host
        if normalized_host is not None:
            if not isinstance(normalized_host, str):
                raise InvalidDatabase("Database host must be a string")
            normalized_host = normalized_host.strip()
            if not normalized_host:
                normalized_host = None
            elif len(normalized_host) > self.MAX_HOST_LENGTH:
                raise InvalidDatabase("Database host is too long")
        if self.port is not None:
            if not isinstance(self.port, int) or isinstance(self.port, bool):
                raise InvalidDatabase("Database port must be an integer")
            if not 1 <= self.port <= 65535:
                raise InvalidDatabase("Database port must be between 1 and 65535")
        object.__setattr__(self, "host", normalized_host)

    def equality_components(self) -> tuple[str | int | None, ...]:
        return (self.host, self.port)
