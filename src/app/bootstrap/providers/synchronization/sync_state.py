from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.use_cases.sync_state import (
    CreateSyncState,
    DeleteSyncState,
    GetSyncState,
    UpdateSyncState,
    UpdateSyncStatus,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemySyncStateRepository,
)


def provide_get_sync_state(session: AsyncSession) -> GetSyncState:
    return GetSyncState(SqlAlchemySyncStateRepository(session))


def provide_create_sync_state(session: AsyncSession) -> CreateSyncState:
    return CreateSyncState(SqlAlchemySyncStateRepository(session))


def provide_update_sync_state(session: AsyncSession) -> UpdateSyncState:
    return UpdateSyncState(SqlAlchemySyncStateRepository(session))


def provide_update_sync_status(session: AsyncSession) -> UpdateSyncStatus:
    return UpdateSyncStatus(SqlAlchemySyncStateRepository(session))


def provide_delete_sync_state(session: AsyncSession) -> DeleteSyncState:
    return DeleteSyncState(SqlAlchemySyncStateRepository(session))
