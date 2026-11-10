from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.common.enums import EntityType
from app.domain.synchronization import SyncStatus


class SyncStateData(Schema):
    id: UUID
    user_id: UUID
    client_device_id: UUID
    updated_at: datetime
    version: int
    entity_type: EntityType | None
    entity_id: UUID | None
    local_version: int | None
    server_version: int | None
    sync_status: SyncStatus
    last_synced_at: datetime | None
    last_error: str | None


class SyncStateCreateRequest(Schema):
    client_device_id: UUID
    entity_type: EntityType | None = None
    entity_id: UUID | None = None
    local_version: int | None = Field(default=None, ge=0, le=2**63 - 1)
    server_version: int | None = Field(default=None, ge=0, le=2**63 - 1)
    status: SyncStatus


class SyncStateUpdateRequest(Schema):
    expected_version: int = Field(ge=0, le=2**63 - 2)
    server_version: int = Field(ge=0, le=2**63 - 1)
    status: SyncStatus
    last_error: str | None


class SyncStateStatusUpdateRequest(Schema):
    status: SyncStatus
