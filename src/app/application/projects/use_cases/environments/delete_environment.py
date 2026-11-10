from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.interfaces import EnvironmentRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteEnvironment:
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
    async def execute(self, identity: VerifiedIdentity, environment_id: UUID) -> None:
        existing = await self._environment_repository.get_by_id(identity, environment_id)
        if existing is None:
            raise EnvironmentNotFound(str(environment_id))
        result = await self._environment_repository.delete(identity, environment_id)
        if not result:
            raise EnvironmentNotFound(str(environment_id))
        await self._recorder.execute(
            identity,
            EntityType.ENVIRONMENT,
            environment_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
