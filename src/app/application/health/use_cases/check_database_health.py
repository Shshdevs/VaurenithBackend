from ..interfaces.health_repository import HealthRepository


class CheckDatabaseHealth:
    def __init__(self, health_checker: HealthRepository) -> None:
        self._health_checker = health_checker

    async def execute(self) -> bool:
        return await self._health_checker.is_available()
