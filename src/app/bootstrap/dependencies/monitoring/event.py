from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateEvent, GetUserEvents
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.monitoring import (
    provide_create_event,
    provide_get_user_events,
)


def create_event_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateEvent:
    return provide_create_event(session)


def get_user_events_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserEvents:
    return provide_get_user_events(session)
