from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.health.use_cases import CheckDatabaseHealth
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.health import provide_database_health_check


def get_database_health_check(
    session: AsyncSession = Depends(get_database_session),
) -> CheckDatabaseHealth:
    return provide_database_health_check(session)
