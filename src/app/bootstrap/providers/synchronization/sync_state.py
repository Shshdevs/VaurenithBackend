from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.use_cases.change_log import RecordChange
from app.application.synchronization.use_cases.sync_state import (
    CreateSyncState,
    DeleteSyncState,
    GetSyncState,
    UpdateSyncState,
    UpdateSyncStatus,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
    SqlAlchemySyncStateRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_get_sync_state(session: AsyncSession) -> GetSyncState:
    return GetSyncState(SqlAlchemySyncStateRepository(session))


def provide_create_sync_state(session: AsyncSession) -> CreateSyncState:
    return CreateSyncState(
        SqlAlchemySyncStateRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_update_sync_state(session: AsyncSession) -> UpdateSyncState:
    return UpdateSyncState(
        SqlAlchemySyncStateRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_update_sync_status(session: AsyncSession) -> UpdateSyncStatus:
    return UpdateSyncStatus(
        SqlAlchemySyncStateRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_sync_state(session: AsyncSession) -> DeleteSyncState:
    return DeleteSyncState(
        SqlAlchemySyncStateRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
