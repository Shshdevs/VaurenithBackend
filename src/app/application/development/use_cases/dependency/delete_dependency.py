from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.exceptions import DependencyNotFound
from app.application.development.interfaces import DependencyRepository
from app.application.identity import VerifiedIdentity


class DeleteDependency:
    def __init__(self, repository: DependencyRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    @transactional
    async def delete_dependency(
        self, identity: VerifiedIdentity, dependency_id: UUID
    ) -> None:
        if not await self._repository.delete(identity.user_id, dependency_id):
            raise DependencyNotFound(str(dependency_id))
