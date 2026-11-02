from typing import Protocol


class DatabaseHealthChecker(Protocol):
    def is_available(self) -> bool: ...
