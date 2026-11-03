from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.monitoring.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ...bootstrap.providers import provide_database_health_check
from .database import get_db


def get_database_health_check(
    session: AsyncSession = Depends(get_db),
) -> CheckDatabaseHealth:
    return provide_database_health_check(session)
