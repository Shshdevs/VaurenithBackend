from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.change_log import GetUserChangeLog
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.synchronization import provide_get_user_change_log


def get_user_change_log_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserChangeLog:
    return provide_get_user_change_log(session)
