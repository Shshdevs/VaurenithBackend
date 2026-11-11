from datetime import datetime
from uuid import UUID

from app.api.schemas.common import Schema


class DeviceGroupMemberData(Schema):
    id: UUID
    group_id: UUID
    device_id: UUID
    created_at: datetime
