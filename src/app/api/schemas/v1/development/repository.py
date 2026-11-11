from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.development.enums import RepositoryType


class RepositoryData(Schema):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    description: str | None
    remote_url: str | None
    default_branch: str | None
    repository_type: RepositoryType
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class RepositoryCreateRequest(Schema):
    name: str = Field(min_length=1, max_length=255)
    repository_type: RepositoryType = RepositoryType.GIT
    description: str | None = None
    remote_url: str | None = None
    default_branch: str | None = Field(default=None, max_length=255)


class RepositoryUpdateRequest(Schema):
    version: int = Field(ge=1, le=2**63 - 2)
    name: str = Field(min_length=1, max_length=255)
    repository_type: RepositoryType
    description: str | None = None
    remote_url: str | None = None
    default_branch: str | None = Field(default=None, max_length=255)
