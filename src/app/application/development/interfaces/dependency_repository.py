from typing import Protocol
from uuid import UUID

from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import DependencyType


class DependencyRepository(Protocol):
    async def get_by_id(self, user_id: UUID, dependency_id: UUID) -> Dependency | None: ...

    async def get_by_component(
        self, user_id: UUID, component_id: UUID
    ) -> list[Dependency]: ...

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[Dependency]: ...

    async def get_by_key(
        self,
        user_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
        dependency_type: DependencyType,
    ) -> Dependency | None: ...

    async def create(self, user_id: UUID, dependency: Dependency) -> None: ...

    async def update(self, user_id: UUID, dependency: Dependency) -> bool: ...

    async def delete(self, user_id: UUID, dependency_id: UUID) -> bool: ...
