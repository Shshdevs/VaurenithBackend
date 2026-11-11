from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.monitoring import LogMetadata


class LogMetadataRepository(Protocol):
    async def create(self, value: LogMetadata) -> None: ...

    async def get_user_log_metadata(
        self,
        user_id: UUID,
        project_id: UUID | None,
        device_id: UUID | None,
        service_id: UUID | None,
        container_id: UUID | None,
        source: str | None,
        severity: str | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[LogMetadata]: ...
