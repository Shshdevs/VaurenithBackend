from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.projects import Environment


@dataclass(frozen=True)
class EnvironmentData:
    id: UUID
    project_id: UUID
    name: str
    slug: str
    environment_type: str
    description: str | None
    configuration: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def from_environment(cls, environment: Environment) -> EnvironmentData:
        return cls(
            id=environment.id,
            project_id=environment.project_id,
            name=environment.name,
            slug=environment.slug,
            environment_type=environment.environment_type,
            description=environment.description,
            configuration=environment.configuration,
            version=environment.version,
            created_at=environment.created_at,
            updated_at=environment.updated_at,
            deleted_at=environment.deleted_at,
        )
