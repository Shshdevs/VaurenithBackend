from datetime import datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.monitoring.dto import LogMetadataData
from app.application.monitoring.interfaces import LogMetadataRepository


class GetUserLogMetadata:
    def __init__(self, repository: LogMetadataRepository) -> None:
        self._repository = repository

    async def get_user_log_metadata(
        self,
        identity: VerifiedIdentity,
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
    ) -> list[LogMetadataData]:
        if any(
            boundary is not None
            and (boundary.tzinfo is None or boundary.utcoffset() is None)
            for boundary in (start, end)
        ):
            raise InvalidInput("Log metadata range boundaries must include a timezone")
        if start is not None and end is not None and start >= end:
            raise InvalidInput("Log metadata range start must precede end")
        values = await self._repository.get_user_log_metadata(
            identity.user_id,
            project_id,
            device_id,
            service_id,
            container_id,
            source,
            severity,
            start,
            end,
            limit,
            offset,
        )
        return [LogMetadataData.from_log_metadata(value) for value in values]
