from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.projects import Environment


class EnvironmentRepository(Protocol):
    async def get_by_id(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> Environment | None: ...

    async def get_active_by_project_id(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Environment]: ...

    async def create(
        self, identity: VerifiedIdentity, environment: Environment
    ) -> bool: ...

    async def update(
        self, identity: VerifiedIdentity, environment: Environment, expected_version: int
    ) -> bool: ...

    async def delete(self, identity: VerifiedIdentity, environment_id: UUID) -> bool: ...
