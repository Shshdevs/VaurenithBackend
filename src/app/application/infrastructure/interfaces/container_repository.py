from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import Container


class ContainerRepository(Protocol):
    async def get_by_user(self, identity: VerifiedIdentity) -> list[Container]: ...

    async def get_by_id(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> Container | None: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Container]: ...

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[Container]: ...

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Container]: ...

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Container]: ...

    async def create(self, identity: VerifiedIdentity, container: Container) -> bool: ...

    async def update(
        self, identity: VerifiedIdentity, container: Container, expected_version: int
    ) -> bool: ...

    async def delete(self, identity: VerifiedIdentity, container_id: UUID) -> bool: ...
