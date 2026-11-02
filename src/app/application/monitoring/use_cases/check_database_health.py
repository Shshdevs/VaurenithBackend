from ...common.interfaces.database_health import DatabaseHealthChecker


class CheckDatabaseHealth:
    def __init__(self, database_health_checker: DatabaseHealthChecker) -> None:
        self._database_health_checker = database_health_checker

    def execute(self) -> bool:
        return self._database_health_checker.is_available()
