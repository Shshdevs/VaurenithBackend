from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.use_cases.change_log import GetUserChangeLog
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)


def provide_get_user_change_log(session: AsyncSession) -> GetUserChangeLog:
    return GetUserChangeLog(SqlAlchemyChangeLogRepository(session))
