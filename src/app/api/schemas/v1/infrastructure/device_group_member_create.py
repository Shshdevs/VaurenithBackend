from uuid import UUID

from app.api.schemas.common import Schema


class DeviceGroupMemberCreateRequest(Schema):
    device_id: UUID
