from uuid import UUID

from app.application.common.exceptions import Conflict
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.exceptions import (
    CodeComponentNotFound,
    CodeComponentVersionConflict,
)
from app.application.development.interfaces import CodeComponentRepository
from app.application.identity import VerifiedIdentity
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteCodeComponent:
    def __init__(
        self,
        repository: CodeComponentRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def delete_code_component(
        self, identity: VerifiedIdentity, component_id: UUID, expected_version: int
    ) -> None:
        component = await self._repository.get_by_id(identity.user_id, component_id)
        if component is None:
            raise CodeComponentNotFound(str(component_id))
        if component.version != expected_version:
            raise CodeComponentVersionConflict(expected_version)
        try:
            if not await self._repository.delete(
                identity.user_id, component_id, expected_version
            ):
                raise CodeComponentVersionConflict(expected_version)
        except ValueError as error:
            raise Conflict(str(error)) from error
        await self._recorder.execute(
            identity,
            EntityType.CODE_COMPONENT,
            component_id,
            ChangeOperation.DELETE,
            expected_version + 1,
        )
