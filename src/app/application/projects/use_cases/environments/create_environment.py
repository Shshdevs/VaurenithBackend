from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.projects.dto import EnvironmentData
from app.application.projects.interfaces import EnvironmentRepository
from app.domain.projects import (
    Environment,
    EnvironmentName,
    EnvironmentType,
    InvalidEnvironment,
)


class CreateEnvironment:
    def __init__(self, environment_repository: EnvironmentRepository) -> None:
        self._environment_repository = environment_repository

    async def execute(
        self,
        project_id: UUID,
        name: str,
        environment_type: EnvironmentType,
        description: str | None = None,
        configuration: dict[str, Any] | None = None,
        version: int = 1,
    ) -> EnvironmentData:
        try:
            environment_name = EnvironmentName(name)
            now = datetime.now(UTC)
            environment = Environment(
                entity_id=uuid4(),
                project_id=project_id,
                name=environment_name,
                environment_type=EnvironmentType(environment_type),
                description=description,
                configuration=configuration,
                version=version,
                created_at=now,
                updated_at=now,
            )
        except (InvalidEnvironment, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._environment_repository.create(environment=environment)
        return EnvironmentData.from_environment(environment=environment)
