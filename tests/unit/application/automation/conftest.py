from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

from app.domain.automation import Script, ScriptExecution, ScriptTarget
from app.domain.automation.enums import ExecutionStatus


class AutomationRepositoryStub:
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.scripts: dict[UUID, Script] = {}
        self.script_owners: dict[UUID, UUID] = {}
        self.targets: dict[UUID, ScriptTarget] = {}
        self.executions: dict[UUID, ScriptExecution] = {}
        self.devices: set[UUID] = set()
        self.client_devices: set[UUID] = set()
        self.environments: dict[UUID, UUID] = {}

    async def get_script(self, user_id: UUID, script_id: UUID) -> Script | None:
        if self.script_owners.get(script_id) != user_id:
            return None
        script = self.scripts.get(script_id)
        return deepcopy(script) if script and script.deleted_at is None else None

    async def get_scripts(self, user_id: UUID) -> list[Script]:
        return [
            deepcopy(script)
            for script_id, script in self.scripts.items()
            if self.script_owners.get(script_id) == user_id and script.deleted_at is None
        ]

    async def create_script(self, user_id: UUID, script: Script) -> None:
        self.scripts[script.id] = script
        self.script_owners[script.id] = user_id

    async def update_script(
        self, user_id: UUID, script: Script, expected_version: int
    ) -> bool:
        current = await self.get_script(user_id, script.id)
        if current is None or current.version != expected_version:
            return False
        self.scripts[script.id] = script
        return True

    async def delete_script(
        self, user_id: UUID, script_id: UUID, expected_version: int
    ) -> bool:
        current = await self.get_script(user_id, script_id)
        if current is None or current.version != expected_version:
            return False
        now = datetime.now(UTC)
        self.scripts[script_id] = Script(
            entity_id=current.id,
            project_id=current.project_id,
            name=current.name,
            description=current.description,
            content=current.content,
            interpreter=current.interpreter,
            execution_type=current.execution_type,
            parameters=current.parameters,
            risk_level=current.risk_level,
            requires_confirmation=current.requires_confirmation,
            version=expected_version + 1,
            created_at=current.created_at,
            updated_at=now,
            deleted_at=now,
        )
        for execution_id, execution in list(self.executions.items()):
            if (
                execution.script_id == script_id
                and execution.status is ExecutionStatus.PENDING
            ):
                execution.cancel(now, "Script was deleted before execution")
                self.executions[execution_id] = execution
        return True

    async def get_targets(self, user_id: UUID, script_id: UUID) -> list[ScriptTarget]:
        if await self.get_script(user_id, script_id) is None:
            return []
        return [
            deepcopy(target)
            for target in self.targets.values()
            if target.script_id == script_id
        ]

    async def create_target(self, user_id: UUID, target: ScriptTarget) -> None:
        script = await self.get_script(user_id, target.script_id)
        if script is None:
            raise ValueError("Script not found")
        if target.device_id not in self.devices:
            raise ValueError("Device not found")
        if target.environment_id is not None:
            if target.environment_id not in self.environments:
                raise ValueError("Environment not found")
            environment_project_id = self.environments[target.environment_id]
            if (
                script.project_id is not None
                and environment_project_id != script.project_id
            ):
                raise ValueError("Environment must belong to the script project")
        if any(
            existing.script_id == target.script_id
            and existing.device_id == target.device_id
            and existing.environment_id == target.environment_id
            for existing in self.targets.values()
        ):
            raise ValueError("Script target already exists")
        self.targets[target.id] = target

    async def delete_target(self, user_id: UUID, script_id: UUID, target_id: UUID) -> bool:
        target = self.targets.get(target_id)
        if (
            target is None
            or target.script_id != script_id
            or self.script_owners.get(script_id) != user_id
        ):
            return False
        del self.targets[target_id]
        return True

    async def create_execution(self, user_id: UUID, execution: ScriptExecution) -> None:
        if await self.get_script(user_id, execution.script_id) is None:
            raise ValueError("Script not found")
        if execution.client_device_id not in self.client_devices:
            raise ValueError("Active client device not found")
        if execution.device_id is not None:
            if execution.device_id not in self.devices:
                raise ValueError("Device not found")
            if not any(
                target.script_id == execution.script_id
                and target.device_id == execution.device_id
                for target in self.targets.values()
            ):
                raise ValueError("Script is not assigned to this device")
        self.executions[execution.id] = execution

    async def get_execution(
        self, user_id: UUID, execution_id: UUID
    ) -> ScriptExecution | None:
        execution = self.executions.get(execution_id)
        if execution is None or self.script_owners.get(execution.script_id) != user_id:
            return None
        return deepcopy(execution)

    async def get_execution_by_idempotency_key(
        self, user_id: UUID, idempotency_key: UUID
    ) -> ScriptExecution | None:
        return next(
            (
                deepcopy(execution)
                for execution in self.executions.values()
                if execution.idempotency_key == idempotency_key
                and self.script_owners.get(execution.script_id) == user_id
            ),
            None,
        )

    async def get_executions(
        self, user_id: UUID, script_id: UUID | None = None
    ) -> list[ScriptExecution]:
        return [
            deepcopy(execution)
            for execution in self.executions.values()
            if self.script_owners.get(execution.script_id) == user_id
            and (script_id is None or execution.script_id == script_id)
        ]

    async def get_pending_executions(
        self, user_id: UUID, client_device_id: UUID
    ) -> list[ScriptExecution]:
        return [
            execution
            for execution in await self.get_executions(user_id)
            if execution.client_device_id == client_device_id
            and execution.status is ExecutionStatus.PENDING
        ]

    async def cancel_pending_for_script(self, user_id: UUID, script_id: UUID) -> None:
        now = datetime.now(UTC)
        for execution_id, execution in list(self.executions.items()):
            if (
                self.script_owners.get(script_id) == user_id
                and execution.script_id == script_id
                and execution.status is ExecutionStatus.PENDING
            ):
                execution.cancel(now, "Script was deleted before execution")
                self.executions[execution_id] = execution

    async def update_execution(
        self,
        user_id: UUID,
        execution: ScriptExecution,
        expected_status: ExecutionStatus,
    ) -> bool:
        current = await self.get_execution(user_id, execution.id)
        if current is None or current.status is not expected_status:
            return False
        self.executions[execution.id] = execution
        return True


class ProjectRepositoryStub:
    def __init__(self, project_ids: set[UUID]) -> None:
        self.project_ids = project_ids

    async def get_by_id(self, user_id: UUID, project_id: UUID):
        return object() if project_id in self.project_ids else None


class ChangeRecorderStub:
    def __init__(self) -> None:
        self.records: list[tuple] = []

    async def execute(self, *args) -> None:
        self.records.append(args)
