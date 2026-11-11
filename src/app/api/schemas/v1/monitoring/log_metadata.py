from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema


class LogMetadataData(Schema):
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


class LogMetadataCreateRequest(Schema):
    source: str = Field(min_length=1, max_length=255)
    project_id: UUID | None = None
    device_id: UUID | None = None
    service_id: UUID | None = None
    container_id: UUID | None = None
    reference: str | None = Field(default=None, max_length=4096)
    description: str | None = Field(default=None, max_length=4000)
    severity: str | None = Field(default=None, max_length=50)
    records_count: int | None = Field(default=None, ge=-(2**63), le=2**63 - 1)
    collected_at: datetime | None = None
