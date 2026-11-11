from datetime import datetime
from uuid import UUID

from app.api.schemas.common import Schema


class ScriptTargetData(Schema):
    id: UUID
    script_id: UUID
    device_id: UUID
    environment_id: UUID | None
    created_at: datetime


class ScriptTargetCreateRequest(Schema):
    device_id: UUID
    environment_id: UUID | None = None
