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
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyConnectionRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_connection(session: AsyncSession) -> CreateConnection:
    return CreateConnection(
        SqlAlchemyConnectionRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_connection(session: AsyncSession) -> GetConnection:
    return GetConnection(SqlAlchemyConnectionRepository(session))


def provide_get_user_connections(session: AsyncSession) -> GetUserConnections:
    return GetUserConnections(SqlAlchemyConnectionRepository(session))


def provide_get_device_connections(session: AsyncSession) -> GetDeviceConnections:
    return GetDeviceConnections(SqlAlchemyConnectionRepository(session))


def provide_update_connection(session: AsyncSession) -> UpdateConnection:
    return UpdateConnection(
        SqlAlchemyConnectionRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_report_connection_status(session: AsyncSession) -> ReportConnectionStatus:
    return ReportConnectionStatus(
        SqlAlchemyConnectionRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_connection(session: AsyncSession) -> DeleteConnection:
    return DeleteConnection(
        SqlAlchemyConnectionRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
