from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import Service


class ServiceRepository(Protocol):
    async def get_by_user(self, identity: VerifiedIdentity) -> list[Service]: ...

    async def get_by_id(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> Service | None: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Service]: ...

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Service]: ...

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Service]: ...

    async def create(self, identity: VerifiedIdentity, service: Service) -> bool: ...

    async def update(
        self, identity: VerifiedIdentity, service: Service, expected_version: int
    ) -> bool: ...

    async def delete(self, identity: VerifiedIdentity, service_id: UUID) -> bool: ...
