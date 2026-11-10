from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.dto import EnvironmentData
from app.application.projects.exceptions import (
    EnvironmentNotFound,
    EnvironmentVersionConflict,
)
from app.application.projects.interfaces import EnvironmentRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.projects import (
    Environment,
    EnvironmentName,
    EnvironmentType,
    InvalidEnvironment,
)
from app.domain.synchronization import ChangeOperation


class UpdateEnvironment:
    def __init__(
        self,
        environment_repository: EnvironmentRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._environment_repository = environment_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        environment_id: UUID,
        project_id: UUID,
        name: str,
        environment_type: EnvironmentType,
        expected_version: int,
        description: str | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> EnvironmentData:
        existing_environment = await self._environment_repository.get_by_id(
            identity=identity, environment_id=environment_id
        )

        if existing_environment is None:
            raise EnvironmentNotFound(str(environment_id))
        if existing_environment.project_id != project_id:
            raise EnvironmentNotFound(str(environment_id))
        if existing_environment.version != expected_version:
            raise EnvironmentVersionConflict(expected_version, existing_environment.version)
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
                version=expected_version + 1,
                created_at=existing_environment.created_at,
                updated_at=now,
                deleted_at=existing_environment.deleted_at,
            )
        except (InvalidEnvironment, ValueError) as error:
            raise InvalidInput(str(error)) from error
        result = await self._environment_repository.update(
            identity, environment, expected_version
        )

        if not result:
            latest = await self._environment_repository.get_by_id(identity, environment_id)
            if latest is None:
                raise EnvironmentNotFound(str(environment_id))
            raise EnvironmentVersionConflict(expected_version, latest.version)
        await self._recorder.execute(
            identity,
            EntityType.ENVIRONMENT,
            environment.id,
            ChangeOperation.UPDATE,
            environment.version,
            {
                "project_id": str(environment.project_id),
                "name": environment.name,
                "environment_type": environment.environment_type.value,
                "description": environment.description,
            },
        )
        return EnvironmentData.from_environment(environment=environment)
