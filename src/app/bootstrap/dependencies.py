from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ..infrastructure.persistence.database import SessionLocal
from .providers import provide_database_health_check


async def get_database_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def get_database_health_check(
    session: AsyncSession = Depends(get_database_session),
) -> CheckDatabaseHealth:
    return provide_database_health_check(session)
