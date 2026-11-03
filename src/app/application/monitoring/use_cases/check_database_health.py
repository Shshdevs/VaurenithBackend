from ...common.interfaces.database_health import HealthChecker


class CheckDatabaseHealth:
    def __init__(self, health_checker: HealthChecker) -> None:
        self._health_checker = health_checker

    async def execute(self) -> bool:
        return await self._health_checker.is_available()
