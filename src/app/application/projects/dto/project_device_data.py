from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.projects import ProjectDevice


@dataclass(frozen=True)
class ProjectDeviceData:
    id: UUID
    project_id: UUID
    device_id: UUID
    role: str | None
    created_at: datetime
    version: int

    @classmethod
    def from_project_device(cls, project_device: ProjectDevice) -> ProjectDeviceData:
        return cls(
            id=project_device.id,
            project_id=project_device.project_id,
            device_id=project_device.device_id,
            role=project_device.role,
            created_at=project_device.created_at,
            version=project_device.version,
        )
