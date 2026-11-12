from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema


class CommitData(Schema):
    id: UUID
    repository_id: UUID
    hash: str
    author_name: str | None
    author_email: str | None
    message: str | None
    committed_at: datetime | None
    changed_files: Any | None
    cached_at: datetime | None


class CommitCreateRequest(Schema):
    hash: str = Field(min_length=40, max_length=64, pattern="^[0-9a-fA-F]+$")
    author_name: str | None = Field(default=None, max_length=255)
    author_email: str | None = Field(default=None, max_length=320)
    message: str | None = None
    committed_at: datetime | None = None
    changed_files: Any | None = None
