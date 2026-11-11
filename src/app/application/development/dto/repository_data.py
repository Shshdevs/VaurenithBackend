from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.development.enums import RepositoryType


@dataclass(frozen=True, slots=True)
class RepositoryData:
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

    @classmethod
    def from_repository(cls, repository) -> "RepositoryData":
        return cls(
            id=repository.id,
            project_id=repository.project_id,
            name=repository.name,
            slug=repository.slug,
            description=repository.description,
            remote_url=repository.remote_url,
            default_branch=repository.default_branch,
            repository_type=repository.repository_type,
            version=repository.version,
            created_at=repository.created_at,
            updated_at=repository.updated_at,
            deleted_at=repository.deleted_at,
        )
