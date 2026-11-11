from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.monitoring import LogMetadata


@dataclass(frozen=True, slots=True)
class LogMetadataData:
    id: UUID
    user_id: UUID
    project_id: UUID | None
    device_id: UUID | None
    service_id: UUID | None
    container_id: UUID | None
    source: str
    reference: str | None
    description: str | None
    severity: str | None
    records_count: int | None
    collected_at: datetime | None
    created_at: datetime

    @classmethod
    def from_log_metadata(cls, value: LogMetadata) -> "LogMetadataData":
        return cls(
            id=value.id,
            user_id=value.user_id,
            project_id=value.project_id,
            device_id=value.device_id,
            service_id=value.service_id,
            container_id=value.container_id,
            source=value.source,
            reference=value.reference,
            description=value.description,
            severity=value.severity,
            records_count=value.records_count,
            collected_at=value.collected_at,
            created_at=value.created_at,
        )
