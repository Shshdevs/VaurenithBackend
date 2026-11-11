from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.infrastructure import DeviceGroupMember


@dataclass(frozen=True)
class DeviceGroupMemberData:
    id: UUID
    group_id: UUID
    device_id: UUID
    created_at: datetime

    @classmethod
    def from_member(cls, member: DeviceGroupMember) -> DeviceGroupMemberData:
        return cls(
            id=member.id,
            group_id=member.group_id,
            device_id=member.device_id,
            created_at=member.created_at,
        )
