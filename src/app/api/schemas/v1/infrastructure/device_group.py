from datetime import datetime
from uuid import UUID

from app.api.schemas.common import Schema


class DeviceGroup(Schema):
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
