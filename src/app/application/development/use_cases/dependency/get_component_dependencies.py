from uuid import UUID

from app.application.development.dto import DependencyData
from app.application.development.exceptions import CodeComponentNotFound
from app.application.development.interfaces import (
    CodeComponentRepository,
    DependencyRepository,
)
from app.application.identity import VerifiedIdentity


class GetComponentDependencies:
    def __init__(
        self,
        dependency_repository: DependencyRepository,
        component_repository: CodeComponentRepository,
    ) -> None:
        self._dependencies = dependency_repository
        self._components = component_repository

    async def get_component_dependencies(
        self, identity: VerifiedIdentity, component_id: UUID
    ) -> list[DependencyData]:
        if await self._components.get_by_id(identity.user_id, component_id) is None:
            raise CodeComponentNotFound(str(component_id))
        dependencies = await self._dependencies.get_by_component(
            identity.user_id, component_id
        )
        return [DependencyData.from_dependency(item) for item in dependencies]
