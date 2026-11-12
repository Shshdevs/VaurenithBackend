from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema


class BranchData(Schema):
    id: UUID
    repository_id: UUID
    name: str
    commit_hash: str | None
    is_remote: bool
    is_current: bool
    last_updated_at: datetime | None
    last_synced_at: datetime | None


class BranchCreateRequest(Schema):
    name: str = Field(min_length=1, max_length=255)
    commit_hash: str | None = Field(default=None, min_length=40, max_length=64)
    is_remote: bool = False
    is_current: bool = False
    last_updated_at: datetime | None = None
    last_synced_at: datetime | None = None


class BranchUpdateRequest(BranchCreateRequest):
    pass
