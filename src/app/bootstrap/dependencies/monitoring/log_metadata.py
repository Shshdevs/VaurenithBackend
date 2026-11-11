from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateLogMetadata, GetUserLogMetadata
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.monitoring import (
    provide_create_log_metadata,
    provide_get_user_log_metadata,
)


def create_log_metadata_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateLogMetadata:
    return provide_create_log_metadata(session)


def get_user_log_metadata_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserLogMetadata:
    return provide_get_user_log_metadata(session)
