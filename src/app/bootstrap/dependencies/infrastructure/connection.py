from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.connection import (
    CreateConnection,
    DeleteConnection,
    GetConnection,
    GetDeviceConnections,
    GetUserConnections,
    ReportConnectionStatus,
    UpdateConnection,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.connections import (
    provide_create_connection,
    provide_delete_connection,
    provide_get_connection,
    provide_get_device_connections,
    provide_get_user_connections,
    provide_report_connection_status,
    provide_update_connection,
)


def get_create_connection_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateConnection:
    return provide_create_connection(session)


def get_get_connection_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetConnection:
    return provide_get_connection(session)


def get_get_user_connections_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserConnections:
    return provide_get_user_connections(session)


def get_get_device_connections_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDeviceConnections:
    return provide_get_device_connections(session)


def get_update_connection_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateConnection:
    return provide_update_connection(session)


def get_report_connection_status_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> ReportConnectionStatus:
    return provide_report_connection_status(session)


def get_delete_connection_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteConnection:
    return provide_delete_connection(session)
