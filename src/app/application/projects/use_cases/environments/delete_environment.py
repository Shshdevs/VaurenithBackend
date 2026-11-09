from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.interfaces import EnvironmentRepository


class DeleteEnvironment:
    def __init__(self, environment_repository: EnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    async def execute(self, identity: VerifiedIdentity, environment_id: UUID) -> None:
        result = await self._environment_repository.delete(identity, environment_id)
        if not result:
            raise EnvironmentNotFound(str(environment_id))
