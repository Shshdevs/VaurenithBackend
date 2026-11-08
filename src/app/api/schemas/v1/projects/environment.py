from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.projects.enums import EnvironmentType


class EnvironmentData(Schema):
    id: UUID
    project_id: UUID
    name: str
    slug: str
    environment_type: EnvironmentType
    description: str | None
    configuration: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
