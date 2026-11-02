from sqlalchemy.orm import Session

from ..application.monitoring.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ..infrastructure.integrations.database.health_checker import (
    SqlAlchemyDatabaseHealthChecker,
)


def provide_database_health_check(session: Session) -> CheckDatabaseHealth:
    return CheckDatabaseHealth(SqlAlchemyDatabaseHealthChecker(session))
