from uuid import UUID

from app.application.projects.dto.environment_data import EnvironmentData
from app.application.projects.interfaces.environment_repository import (
    EnvironmentRepository,
)


class GetProjectEnvironments:
    def __init__(self, environment_repository: EnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    async def execute(self, project_id: UUID) -> list[EnvironmentData]:
        environments = await self._environment_repository.get_active_by_project_id(
            project_id=project_id
        )
        return [
            EnvironmentData.from_environment(environment) for environment in environments
        ]
