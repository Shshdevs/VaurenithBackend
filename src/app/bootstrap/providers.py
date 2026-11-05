from sqlalchemy.ext.asyncio import AsyncSession

from ..application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ..infrastructure.integrations.database.health_checker import (
    SqlAlchemyHealthChecker,
)


def provide_database_health_check(session: AsyncSession) -> CheckDatabaseHealth:
    return CheckDatabaseHealth(SqlAlchemyHealthChecker(session))
