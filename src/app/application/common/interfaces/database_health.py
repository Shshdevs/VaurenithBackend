from typing import Protocol


class DatabaseHealthChecker(Protocol):
    async def is_available(self) -> bool: ...
