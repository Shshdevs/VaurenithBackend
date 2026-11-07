from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


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
