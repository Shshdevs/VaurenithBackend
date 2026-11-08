from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.projects.dto import EnvironmentData
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.interfaces import EnvironmentRepository
from app.domain.projects import (
    Environment,
    EnvironmentName,
    EnvironmentType,
    InvalidEnvironment,
)


class UpdateEnvironment:
    def __init__(self, environment_repository: EnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    async def execute(
        self,
        environment_id: UUID,
        project_id: UUID,
        name: str,
        environment_type: EnvironmentType,
        description: str | None = None,
        configuration: dict[str, Any] | None = None,
        version: int = 1,
    ) -> EnvironmentData:
        existing_environment = await self._environment_repository.get_by_id(
            environment_id=environment_id
        )

        if existing_environment is None:
            raise EnvironmentNotFound(str(environment_id))
        try:
            environment_name = EnvironmentName(name)
            now = datetime.now(UTC)
            environment = Environment(
                entity_id=environment_id,
                project_id=project_id,
                name=environment_name,
                environment_type=EnvironmentType(environment_type),
                description=description,
                configuration=configuration,
                version=version,
                created_at=existing_environment.created_at,
                updated_at=now,
                deleted_at=existing_environment.deleted_at,
            )
        except (InvalidEnvironment, ValueError) as error:
            raise InvalidInput(str(error)) from error
        result = await self._environment_repository.update(environment=environment)

        if not result:
            raise EnvironmentNotFound(str(environment_id))
        return EnvironmentData.from_environment(environment=environment)
