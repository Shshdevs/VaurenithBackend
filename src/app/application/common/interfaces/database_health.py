from typing import Protocol


class HealthChecker(Protocol):
    async def is_available(self) -> bool: ...
