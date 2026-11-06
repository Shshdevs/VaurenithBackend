from dataclasses import dataclass
from typing import ClassVar

from app.domain.common.value_object import ValueObject
from app.domain.infrastructure.exceptions import InvalidConnection


@dataclass(frozen=True, slots=True, eq=False)
class ConnectionEndpoint(ValueObject):
    MAX_HOST_LENGTH: ClassVar[int] = 512
    host: str
    port: int = 22

    def __post_init__(self) -> None:
        if not isinstance(self.host, str):
            raise InvalidConnection("Connection host must be a string")
        normalized_host = self.host.strip()
        if not normalized_host or len(normalized_host) > self.MAX_HOST_LENGTH:
            raise InvalidConnection("Connection host is invalid")
        if not isinstance(self.port, int) or isinstance(self.port, bool):
            raise InvalidConnection("Connection port must be an integer")
        if not 1 <= self.port <= 65535:
            raise InvalidConnection("Connection port must be between 1 and 65535")
        object.__setattr__(self, "host", normalized_host)

    def equality_components(self) -> tuple[str | int, ...]:
        return (self.host, self.port)
