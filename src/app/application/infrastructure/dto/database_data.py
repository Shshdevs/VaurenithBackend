from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.infrastructure import Database
from app.domain.infrastructure.enums import DbmsType, ResourceStatus


@dataclass(frozen=True)
class DatabaseData:
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    container_id: UUID | None
    service_id: UUID | None
    name: str
    slug: str
    dbms_type: DbmsType
    host: str | None
    port: int | None
    database_name: str | None
    status: ResourceStatus
    last_checked_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_database(cls, database: Database) -> DatabaseData:
        return cls(
            id=database.id,
            project_id=database.project_id,
            environment_id=database.environment_id,
            device_id=database.device_id,
            container_id=database.container_id,
            service_id=database.service_id,
            name=database.name,
            slug=database.slug,
            dbms_type=database.dbms_type,
            host=database.host,
            port=database.port,
            database_name=database.database_name,
            status=database.status,
            last_checked_at=database.last_checked_at,
            metadata=database.metadata,
            version=database.version,
            created_at=database.created_at,
            updated_at=database.updated_at,
        )
