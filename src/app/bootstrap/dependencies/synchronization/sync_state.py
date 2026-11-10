from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.use_cases.sync_state import (
    CreateSyncState,
    DeleteSyncState,
    GetSyncState,
    UpdateSyncState,
    UpdateSyncStatus,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.synchronization import (
    provide_create_sync_state,
    provide_delete_sync_state,
    provide_get_sync_state,
    provide_update_sync_state,
    provide_update_sync_status,
)


def create_sync_state_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateSyncState:
    return provide_create_sync_state(session)


def get_sync_state_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetSyncState:
    return provide_get_sync_state(session)


def update_sync_state_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateSyncState:
    return provide_update_sync_state(session)


def update_sync_status_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateSyncStatus:
    return provide_update_sync_status(session)


def delete_sync_state_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteSyncState:
    return provide_delete_sync_state(session)
