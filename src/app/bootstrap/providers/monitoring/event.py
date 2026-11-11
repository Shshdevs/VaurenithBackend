from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateEvent, GetUserEvents
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.persistence.repositories.monitoring import (
    SqlAlchemyEventRepository,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_event(session: AsyncSession) -> CreateEvent:
    return CreateEvent(
        SqlAlchemyEventRepository(session),
        SqlAlchemyDeviceRepository(session),
        SqlAlchemyProjectRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_user_events(session: AsyncSession) -> GetUserEvents:
    return GetUserEvents(SqlAlchemyEventRepository(session))
