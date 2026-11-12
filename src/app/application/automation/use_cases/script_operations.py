from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.automation.dto import ScriptChangeLogData, ScriptData
from app.application.automation.interfaces import (
    ScriptExecutionRepository,
    ScriptRepository,
)
from app.application.common.exceptions import Conflict, InvalidInput, NotFound
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.automation import Script
from app.domain.automation.enums import ScriptExecutionType, ScriptRiskLevel
from app.domain.automation.exceptions import InvalidScript
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class ScriptOperations:
    def __init__(
        self,
        repository: ScriptRepository,
        projects: ProjectRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
        executions: ScriptExecutionRepository | None = None,
    ) -> None:
        self._repository = repository
        self._executions = executions
        self._projects = projects
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    async def list(self, identity: VerifiedIdentity) -> list[ScriptData]:
        return [
            ScriptData.from_script(script)
            for script in await self._repository.get_scripts(identity.user_id)
        ]

    async def get(self, identity: VerifiedIdentity, script_id: UUID) -> ScriptData:
        script = await self._repository.get_script(identity.user_id, script_id)
        if script is None:
            raise NotFound(f"Script {script_id} not found")
        return ScriptData.from_script(script)

    @transactional
    async def create(
        self,
        identity: VerifiedIdentity,
        name: str,
        content: str,
        execution_type: ScriptExecutionType,
        project_id: UUID | None = None,
        description: str | None = None,
        interpreter: str | None = None,
        parameters=None,
        risk_level: ScriptRiskLevel = ScriptRiskLevel.SAFE,
        requires_confirmation: bool = False,
    ) -> ScriptData:
        if (
            project_id is not None
            and await self._projects.get_by_id(identity.user_id, project_id) is None
        ):
            raise ProjectNotFound(str(project_id))
        now = datetime.now(UTC)
        try:
            script = Script(
                entity_id=uuid4(),
                project_id=project_id,
                name=name,
                description=description,
                content=content,
                interpreter=interpreter,
                execution_type=execution_type,
                parameters=parameters,
                risk_level=risk_level,
                requires_confirmation=requires_confirmation,
                created_at=now,
                updated_at=now,
            )
        except (InvalidScript, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._repository.create_script(identity.user_id, script)
        await self._record(identity, script, ChangeOperation.INSERT)
        return ScriptData.from_script(script)

    @transactional
    async def update(
        self,
        identity: VerifiedIdentity,
        script_id: UUID,
        expected_version: int,
        name: str,
        content: str,
        execution_type: ScriptExecutionType,
        project_id: UUID | None = None,
        description: str | None = None,
        interpreter: str | None = None,
        parameters=None,
        risk_level: ScriptRiskLevel = ScriptRiskLevel.SAFE,
        requires_confirmation: bool = False,
    ) -> ScriptData:
        current = await self._repository.get_script(identity.user_id, script_id)
        if current is None:
            raise NotFound(f"Script {script_id} not found")
        if current.version != expected_version:
            raise Conflict("Script version conflict")
        if (
            project_id is not None
            and await self._projects.get_by_id(identity.user_id, project_id) is None
        ):
            raise ProjectNotFound(str(project_id))
        now = datetime.now(UTC)
        try:
            updated = Script(
                entity_id=current.id,
                project_id=project_id,
                name=name,
                description=description,
                content=content,
                interpreter=interpreter,
                execution_type=execution_type,
                parameters=parameters,
                risk_level=risk_level,
                requires_confirmation=requires_confirmation,
                version=expected_version + 1,
                created_at=current.created_at,
                updated_at=now,
            )
        except (InvalidScript, ValueError) as error:
            raise InvalidInput(str(error)) from error
        if not await self._repository.update_script(
            identity.user_id, updated, expected_version
        ):
            raise Conflict("Script version conflict")
        await self._record(identity, updated, ChangeOperation.UPDATE)
        return ScriptData.from_script(updated)

    @transactional
    async def delete(
        self, identity: VerifiedIdentity, script_id: UUID, expected_version: int
    ) -> None:
        if not await self._repository.delete_script(
            identity.user_id, script_id, expected_version
        ):
            script = await self._repository.get_script(identity.user_id, script_id)
            if script is None:
                raise NotFound(f"Script {script_id} not found")
            raise Conflict("Script version conflict")
        if self._executions is not None:
            await self._executions.cancel_pending_for_script(identity.user_id, script_id)
        await self._recorder.execute(
            identity,
            EntityType.SCRIPT,
            script_id,
            ChangeOperation.DELETE,
            expected_version + 1,
        )

    async def _record(self, identity: VerifiedIdentity, script: Script, operation) -> None:
        await self._recorder.execute(
            identity,
            EntityType.SCRIPT,
            script.id,
            operation,
            script.version,
            ScriptChangeLogData.from_script(script).to_payload(),
        )
