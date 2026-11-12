from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.projects import ProjectDevice


class ProjectDeviceRepository(Protocol):
    async def get_by_id(
        self, identity: VerifiedIdentity, project_device_id: UUID
    ) -> ProjectDevice | None: ...

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[ProjectDevice]: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ProjectDevice]: ...

    async def link(
        self, identity: VerifiedIdentity, project_device: ProjectDevice
    ) -> bool: ...

    async def update(
        self,
        identity: VerifiedIdentity,
        project_device: ProjectDevice,
        expected_version: int,
    ) -> int | None: ...

    async def delete(self, identity: VerifiedIdentity, project_device_id: UUID) -> bool: ...
