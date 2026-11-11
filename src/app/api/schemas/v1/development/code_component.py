from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.development.enums import ComponentType


class CodeComponentData(Schema):
    id: UUID
    repository_id: UUID
    parent_id: UUID | None
    name: str
    path: str
    component_type: ComponentType
    language: str | None
    symbol: str | None
    start_line: int | None
    end_line: int | None
    analysis_version: str | None
    analyzed_at: datetime | None
    source_commit_hash: str | None
    created_at: datetime
    updated_at: datetime
    version: int


class CodeComponentCreateRequest(Schema):
    parent_id: UUID | None = None
    name: str = Field(min_length=1, max_length=512)
    path: str = Field(min_length=1)
    component_type: ComponentType
    language: str | None = Field(default=None, max_length=100)
    symbol: str | None = Field(default=None, max_length=512)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    analysis_version: str | None = Field(default=None, max_length=100)
    analyzed_at: datetime | None = None
    source_commit_hash: str | None = Field(default=None, min_length=40, max_length=64)


class CodeComponentUpdateRequest(CodeComponentCreateRequest):
    version: int = Field(ge=1, le=2**63 - 2)
