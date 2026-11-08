from uuid import UUID

from app.application.projects.dto import EnvironmentData
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.interfaces import EnvironmentRepository


class GetEnvironment:
    def __init__(self, environment_repository: EnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    async def execute(self, environment_id: UUID) -> EnvironmentData:
        environment = await self._environment_repository.get_by_id(
            environment_id=environment_id
        )
        if not environment:
            raise EnvironmentNotFound(str(environment_id))
        return EnvironmentData.from_environment(environment)
