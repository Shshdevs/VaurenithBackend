from typing import Protocol


class HealthRepository(Protocol):
    async def is_available(self) -> bool: ...
