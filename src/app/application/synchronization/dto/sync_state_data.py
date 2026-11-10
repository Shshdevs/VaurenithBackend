from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.common.enums import EntityType
from app.domain.synchronization import SyncState, SyncStatus


@dataclass(frozen=True)
class SyncStateData:
    id: UUID
    user_id: UUID
    client_device_id: UUID
    updated_at: datetime
    entity_type: EntityType | None
    entity_id: UUID | None
    local_version: int | None
    server_version: int | None
    sync_status: SyncStatus
    last_synced_at: datetime | None
    last_error: str | None

    @classmethod
    def from_sync_state(cls, sync_state: SyncState) -> SyncStateData:
        return SyncStateData(
            id=sync_state.id,
            user_id=sync_state.user_id,
            client_device_id=sync_state.client_device_id,
            updated_at=sync_state.updated_at,
            entity_type=sync_state.entity_type,
            entity_id=sync_state.entity_id,
            local_version=sync_state.local_version,
            server_version=sync_state.server_version,
            sync_status=sync_state.status,
            last_synced_at=sync_state.last_synced_at,
            last_error=sync_state.last_error,
        )
