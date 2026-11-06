from sqlalchemy.ext.asyncio import AsyncSession

from app.application.health.use_cases import CheckDatabaseHealth
from app.infrastructure.integrations.database import SqlAlchemyHealthChecker


def provide_database_health_check(session: AsyncSession) -> CheckDatabaseHealth:
    return CheckDatabaseHealth(SqlAlchemyHealthChecker(session))
