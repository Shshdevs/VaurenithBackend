from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.automation.dto import ScriptTargetData
from app.application.automation.interfaces import ScriptRepository, ScriptTargetRepository
from app.application.common.exceptions import Conflict, NotFound
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.domain.automation import ScriptTarget
from app.domain.automation.exceptions import InvalidScriptTarget


class TargetOperations:
    def __init__(
        self,
        scripts: ScriptRepository,
        repository: ScriptTargetRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._scripts = scripts
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def list(
        self, identity: VerifiedIdentity, script_id: UUID
    ) -> list[ScriptTargetData]:
        if await self._scripts.get_script(identity.user_id, script_id) is None:
            raise NotFound(f"Script {script_id} not found")
        return [
            ScriptTargetData.from_target(target)
            for target in await self._repository.get_targets(identity.user_id, script_id)
        ]

    @transactional
    async def add(
        self,
        identity: VerifiedIdentity,
        script_id: UUID,
        device_id: UUID,
        environment_id: UUID | None = None,
    ) -> ScriptTargetData:
        if await self._scripts.get_script(identity.user_id, script_id) is None:
            raise NotFound(f"Script {script_id} not found")
        try:
            target = ScriptTarget(
                entity_id=uuid4(),
                script_id=script_id,
                device_id=device_id,
                environment_id=environment_id,
                created_at=datetime.now(UTC),
            )
            await self._repository.create_target(identity.user_id, target)
        except (InvalidScriptTarget, ValueError) as error:
            raise Conflict(str(error)) from error
        return ScriptTargetData.from_target(target)

    @transactional
    async def remove(
        self,
        identity: VerifiedIdentity,
        script_id: UUID,
        target_id: UUID,
    ) -> None:
        if not await self._repository.delete_target(identity.user_id, script_id, target_id):
            raise NotFound(f"Script target {target_id} not found")
