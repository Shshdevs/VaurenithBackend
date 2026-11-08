from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.projects import Project


@dataclass(frozen=True)
class ProjectData:
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    project_type: str
    status: str
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def from_project(cls, project: Project) -> ProjectData:
        return cls(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            project_type=project.project_type.value,
            status=project.status.value,
            metadata=project.metadata,
            version=project.version,
            created_at=project.created_at,
            updated_at=project.updated_at,
            deleted_at=project.deleted_at,
        )
