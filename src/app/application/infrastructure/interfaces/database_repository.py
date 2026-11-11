from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import Database


class DatabaseRepository(Protocol):
    async def get_by_user(self, identity: VerifiedIdentity) -> list[Database]: ...

    async def get_by_id(
        self, identity: VerifiedIdentity, database_id: UUID
    ) -> Database | None: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Database]: ...

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Database]: ...

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Database]: ...

    async def get_by_container(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> list[Database]: ...

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[Database]: ...

    async def create(self, identity: VerifiedIdentity, database: Database) -> bool: ...

    async def update(
        self, identity: VerifiedIdentity, database: Database, expected_version: int
    ) -> bool: ...

    async def delete(self, identity: VerifiedIdentity, database_id: UUID) -> bool: ...
