from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.health.use_cases import CheckDatabaseHealth
from ..providers import provide_database_health_check
from .database import get_database_session


def get_database_health_check(
    session: AsyncSession = Depends(get_database_session),
) -> CheckDatabaseHealth:
    return provide_database_health_check(session)
