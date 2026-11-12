from uuid import UUID

from app.application.development.dto import DependencyData
from app.application.development.exceptions import DependencyNotFound
from app.application.development.interfaces import DependencyRepository
from app.application.identity import VerifiedIdentity


class GetDependency:
    def __init__(self, repository: DependencyRepository) -> None:
        self._repository = repository

    async def get_dependency(
        self, identity: VerifiedIdentity, dependency_id: UUID
    ) -> DependencyData:
        dependency = await self._repository.get_by_id(identity.user_id, dependency_id)
        if dependency is None:
            raise DependencyNotFound(str(dependency_id))
        return DependencyData.from_dependency(dependency)
