from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.unit.application.automation.conftest import (
    AutomationRepositoryStub,
    ChangeRecorderStub,
    ProjectRepositoryStub,
)

from app.application.automation import (
    AddScriptTarget,
    CreateScript,
    DeleteScript,
    GetPendingScriptExecutions,
    GetScript,
    GetScriptExecution,
    GetScriptExecutions,
    GetScriptTargets,
    GetUserScripts,
    RemoveScriptTarget,
    ReportScriptExecutionResult,
    RequestScriptExecution,
    StartScriptExecution,
    UpdateScript,
)
from app.application.common.exceptions import Conflict, InvalidInput, NotFound
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.domain.automation.enums import (
    ExecutionStatus,
    ScriptExecutionType,
    ScriptRiskLevel,
)
from app.domain.identity import EmailAddress, TokenHash


def make_identity(user_id=None) -> VerifiedIdentity:
    user_id = user_id or uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="automation-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_use_cases(identity: VerifiedIdentity, projects: set | None = None):
    repository = AutomationRepositoryStub(identity.user_id)
    project_repository = ProjectRepositoryStub(projects or set())
    recorder = ChangeRecorderStub()
    unit_of_work = NoOpUnitOfWork()
    scripts = {
        "create": CreateScript(
            repository, project_repository, recorder, unit_of_work, repository
        ),
        "get": GetScript(
            repository, project_repository, recorder, unit_of_work, repository
        ),
        "list": GetUserScripts(
            repository, project_repository, recorder, unit_of_work, repository
        ),
        "update": UpdateScript(
            repository, project_repository, recorder, unit_of_work, repository
        ),
        "delete": DeleteScript(
            repository, project_repository, recorder, unit_of_work, repository
        ),
    }
    targets = {
        "add": AddScriptTarget(repository, repository, unit_of_work),
        "get": GetScriptTargets(repository, repository, unit_of_work),
        "remove": RemoveScriptTarget(repository, repository, unit_of_work),
    }
    executions = {
        "request": RequestScriptExecution(repository, repository, unit_of_work),
        "pending": GetPendingScriptExecutions(repository, repository, unit_of_work),
        "start": StartScriptExecution(repository, repository, unit_of_work),
        "finish": ReportScriptExecutionResult(repository, repository, unit_of_work),
        "get": GetScriptExecution(repository, repository, unit_of_work),
        "list": GetScriptExecutions(repository, repository, unit_of_work),
    }
    return repository, recorder, scripts, targets, executions


async def create_script(scripts, identity, **overrides):
    values = {
        "name": "Deploy service",
        "content": "echo deploy",
        "execution_type": ScriptExecutionType.LOCAL,
        "project_id": None,
        "description": None,
        "interpreter": None,
        "parameters": None,
        "risk_level": ScriptRiskLevel.SAFE,
        "requires_confirmation": False,
    }
    values.update(overrides)
    return await scripts["create"].create(identity, **values)


@pytest.mark.anyio
async def test_script_create_list_get_and_change_log_payload() -> None:
    identity = make_identity()
    repository, recorder, scripts, _, _ = make_use_cases(identity)

    created = await create_script(scripts, identity)
    listed = await scripts["list"].get_user_scripts(identity)
    fetched = await scripts["get"].get(identity, created.id)

    assert created.version == 1
    assert listed == [created]
    assert fetched == created
    assert recorder.records[0][1].value == "script"
    assert recorder.records[0][5]["content"] == "echo deploy"
    assert repository.script_owners[created.id] == identity.user_id


@pytest.mark.anyio
async def test_script_creation_checks_project_and_domain_rules() -> None:
    identity = make_identity()
    project_id = uuid4()
    _, _, scripts, _, _ = make_use_cases(identity, {project_id})

    created = await create_script(scripts, identity, project_id=project_id)
    assert created.project_id == project_id

    with pytest.raises(ProjectNotFound):
        await create_script(scripts, identity, project_id=uuid4())
    with pytest.raises(InvalidInput):
        await create_script(scripts, identity, name="  ")
    with pytest.raises(InvalidInput):
        await create_script(
            scripts,
            identity,
            risk_level=ScriptRiskLevel.DANGEROUS,
            requires_confirmation=False,
        )


@pytest.mark.anyio
async def test_script_update_is_versioned_and_delete_is_soft() -> None:
    identity = make_identity()
    repository, recorder, scripts, _, _ = make_use_cases(identity)
    created = await create_script(scripts, identity)

    updated = await scripts["update"].update(
        identity,
        created.id,
        1,
        name="Deploy updated",
        content="echo updated",
        execution_type=ScriptExecutionType.LOCAL,
    )
    assert updated.version == 2
    assert updated.content == "echo updated"
    with pytest.raises(Conflict):
        await scripts["update"].update(
            identity,
            created.id,
            1,
            name="Stale",
            content="echo stale",
            execution_type=ScriptExecutionType.LOCAL,
        )

    await scripts["delete"].delete(identity, created.id, 2)
    assert repository.scripts[created.id].deleted_at is not None
    assert recorder.records[-1][3].value == "delete"
    with pytest.raises(NotFound):
        await scripts["get"].get(identity, created.id)


@pytest.mark.anyio
async def test_scripts_are_isolated_by_user() -> None:
    owner = make_identity()
    _, _, owner_scripts, _, _ = make_use_cases(owner)
    created = await create_script(owner_scripts, owner)
    other = make_identity()
    _, _, other_scripts, _, _ = make_use_cases(other)

    with pytest.raises(NotFound):
        await other_scripts["get"].get(other, created.id)


@pytest.mark.anyio
async def test_targets_check_ownership_project_and_duplicates() -> None:
    identity = make_identity()
    project_id = uuid4()
    repository, _, scripts, targets, _ = make_use_cases(identity, {project_id})
    script = await create_script(scripts, identity, project_id=project_id)
    device_id = uuid4()
    environment_id = uuid4()
    repository.devices.add(device_id)
    repository.environments[environment_id] = project_id

    target = await targets["add"].add_script_target(
        identity, script.id, device_id, environment_id
    )
    assert await targets["get"].get_script_targets(identity, script.id) == [target]
    with pytest.raises(Conflict):
        await targets["add"].add_script_target(
            identity, script.id, device_id, environment_id
        )
    with pytest.raises(Conflict):
        await targets["add"].add_script_target(identity, script.id, uuid4())

    repository.environments[uuid4()] = uuid4()
    unrelated_environment_id = next(
        key for key, value in repository.environments.items() if value != project_id
    )
    with pytest.raises(Conflict):
        await targets["add"].add_script_target(
            identity, script.id, uuid4(), unrelated_environment_id
        )

    await targets["remove"].remove_script_target(identity, script.id, target.id)
    assert await targets["get"].get_script_targets(identity, script.id) == []


@pytest.mark.anyio
async def test_execution_confirmation_assignment_and_idempotency() -> None:
    identity = make_identity()
    repository, _, scripts, targets, executions = make_use_cases(identity)
    script = await create_script(
        scripts,
        identity,
        risk_level=ScriptRiskLevel.CRITICAL,
        requires_confirmation=True,
    )
    client_device_id = uuid4()
    device_id = uuid4()
    repository.client_devices.add(client_device_id)
    repository.devices.add(device_id)

    with pytest.raises(InvalidInput):
        await executions["request"].request_script_execution(
            identity, script.id, client_device_id, None, None, None, False
        )
    with pytest.raises(Conflict):
        await executions["request"].request_script_execution(
            identity, script.id, client_device_id, device_id, None, None, True
        )

    await targets["add"].add_script_target(identity, script.id, device_id)
    idempotency_key = uuid4()
    requested = await executions["request"].request_script_execution(
        identity,
        script.id,
        client_device_id,
        device_id,
        {"region": "test"},
        idempotency_key,
        True,
    )
    replay = await executions["request"].request_script_execution(
        identity,
        script.id,
        client_device_id,
        device_id,
        {"region": "different"},
        idempotency_key,
        True,
    )
    assert requested.id == replay.id
    assert requested.status is ExecutionStatus.PENDING
    assert len(repository.executions) == 1

    with pytest.raises(Conflict):
        await executions["request"].request_script_execution(
            identity,
            script.id,
            uuid4(),
            device_id,
            None,
            idempotency_key,
            True,
        )


@pytest.mark.anyio
async def test_execution_queue_start_completion_and_history() -> None:
    identity = make_identity()
    repository, _, scripts, _, executions = make_use_cases(identity)
    script = await create_script(scripts, identity)
    client_device_id = uuid4()
    repository.client_devices.add(client_device_id)
    requested = await executions["request"].request_script_execution(
        identity, script.id, client_device_id, None, None, None, False
    )

    pending = await executions["pending"].get_pending_script_executions(
        identity, client_device_id
    )
    assert [item.id for item in pending] == [requested.id]
    started = await executions["start"].start_script_execution(
        identity, requested.id, client_device_id
    )
    assert started.status is ExecutionStatus.RUNNING
    assert started.started_at is not None
    with pytest.raises(Conflict):
        await executions["start"].start_script_execution(
            identity, requested.id, client_device_id
        )

    finished = await executions["finish"].report_script_execution_result(
        identity,
        requested.id,
        client_device_id,
        "completed",
        0,
        None,
        "Completed without errors",
    )
    assert finished.status is ExecutionStatus.COMPLETED
    assert finished.finished_at is not None
    assert finished.sanitized_output_summary == "Completed without errors"
    assert await executions["get"].get_script_execution(identity, requested.id) == finished
    assert await executions["list"].get_script_executions(identity, script.id) == [finished]
    assert (
        await executions["pending"].get_pending_script_executions(
            identity, client_device_id
        )
        == []
    )


@pytest.mark.anyio
async def test_execution_failure_cancellation_and_terminal_state_rules() -> None:
    identity = make_identity()
    repository, _, scripts, _, executions = make_use_cases(identity)
    script = await create_script(scripts, identity)
    client_device_id = uuid4()
    repository.client_devices.add(client_device_id)

    failed = await executions["request"].request_script_execution(
        identity, script.id, client_device_id, None, None, None, False
    )
    failure = await executions["finish"].report_script_execution_result(
        identity, failed.id, client_device_id, "failed", 1, "process failed", None
    )
    assert failure.status is ExecutionStatus.FAILED
    with pytest.raises(Conflict):
        await executions["finish"].report_script_execution_result(
            identity, failed.id, client_device_id, "completed", 0, None, None
        )

    cancelled = await executions["request"].request_script_execution(
        identity, script.id, client_device_id, None, None, None, False
    )
    result = await executions["finish"].report_script_execution_result(
        identity, cancelled.id, client_device_id, "cancelled", None, "cancelled", None
    )
    assert result.status is ExecutionStatus.CANCELLED


@pytest.mark.anyio
async def test_execution_timeout_and_invalid_result_transition() -> None:
    identity = make_identity()
    repository, _, scripts, _, executions = make_use_cases(identity)
    script = await create_script(scripts, identity)
    client_device_id = uuid4()
    repository.client_devices.add(client_device_id)
    requested = await executions["request"].request_script_execution(
        identity, script.id, client_device_id, None, None, None, False
    )

    with pytest.raises(Conflict):
        await executions["finish"].report_script_execution_result(
            identity, requested.id, client_device_id, "completed", 0, None, None
        )
    with pytest.raises(InvalidInput):
        await executions["finish"].report_script_execution_result(
            identity, requested.id, client_device_id, "running", None, None, None
        )
    assert repository.executions[requested.id].status is ExecutionStatus.PENDING

    await executions["start"].start_script_execution(
        identity, requested.id, client_device_id
    )
    timed_out = await executions["finish"].report_script_execution_result(
        identity,
        requested.id,
        client_device_id,
        "timeout",
        None,
        "Execution timed out",
        None,
    )
    assert timed_out.status is ExecutionStatus.TIMEOUT
    assert timed_out.finished_at is not None


@pytest.mark.anyio
async def test_execution_is_scoped_to_owner_and_client_device() -> None:
    owner = make_identity()
    repository, _, scripts, _, executions = make_use_cases(owner)
    script = await create_script(scripts, owner)
    client_device_id = uuid4()
    repository.client_devices.add(client_device_id)
    requested = await executions["request"].request_script_execution(
        owner, script.id, client_device_id, None, None, None, False
    )
    other = make_identity()
    _, _, _, _, other_executions = make_use_cases(other)

    with pytest.raises(NotFound):
        await executions["start"].start_script_execution(owner, requested.id, uuid4())
    with pytest.raises(NotFound):
        await other_executions["get"].get_script_execution(other, requested.id)


@pytest.mark.anyio
async def test_deleting_script_cancels_pending_executions() -> None:
    identity = make_identity()
    repository, _, scripts, _, executions = make_use_cases(identity)
    script = await create_script(scripts, identity)
    client_device_id = uuid4()
    repository.client_devices.add(client_device_id)
    pending = await executions["request"].request_script_execution(
        identity, script.id, client_device_id, None, None, None, False
    )

    await scripts["delete"].delete(identity, script.id, 1)

    stored = repository.executions[pending.id]
    assert stored.status is ExecutionStatus.CANCELLED
    assert stored.finished_at is not None
