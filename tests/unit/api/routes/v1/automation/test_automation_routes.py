from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.automation import build_automation_router
from app.application.automation.dto import ScriptData, ScriptExecutionData
from app.application.common.exceptions import Conflict
from app.application.identity import VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.domain.automation.enums import (
    ExecutionStatus,
    ScriptExecutionType,
    ScriptRiskLevel,
)
from app.domain.identity import EmailAddress, TokenHash


class CreateScriptStub:
    def __init__(self, script: ScriptData, conflict: bool = False) -> None:
        self.script = script
        self.conflict = conflict
        self.arguments = None

    async def create(self, identity, **values):
        self.arguments = (identity, values)
        if self.conflict:
            raise Conflict("Script version conflict")
        return self.script


class GetUserScriptsStub:
    async def get_user_scripts(self, _identity):
        return []


class GetPendingExecutionsStub:
    def __init__(self, executions):
        self.executions = executions

    async def get_pending_script_executions(self, _identity, _client_device_id):
        return self.executions


class GetScriptStub:
    def __init__(self, script):
        self.script = script

    async def get(self, _identity, _script_id):
        return self.script


def make_script_data() -> ScriptData:
    now = datetime.now(UTC)
    return ScriptData(
        id=uuid4(),
        project_id=None,
        name="Deploy service",
        slug="deploy-service",
        description=None,
        content="echo deploy",
        interpreter=None,
        execution_type=ScriptExecutionType.LOCAL,
        parameters=None,
        risk_level=ScriptRiskLevel.SAFE,
        requires_confirmation=False,
        version=1,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def build_test_client(
    create_script: CreateScriptStub,
    get_user_scripts=None,
    pending_executions=None,
    get_script=None,
    identity_error: bool = False,
) -> TestClient:
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("automation@example.test"),
        auth_provider="automation-route-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )

    def provide_identity():
        if identity_error:
            raise InvalidIdentity("Bearer token is required")
        return identity

    def unused_dependency():
        return object()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_automation_router(
            lambda: create_script,
            lambda: get_script or GetScriptStub(make_script_data()),
            lambda: get_user_scripts or GetUserScriptsStub(),
            unused_dependency,
            unused_dependency,
            unused_dependency,
            unused_dependency,
            unused_dependency,
            unused_dependency,
            lambda: pending_executions or GetPendingExecutionsStub([]),
            unused_dependency,
            unused_dependency,
            unused_dependency,
            unused_dependency,
            provide_identity,
        )
    )
    return TestClient(app)


def test_post_script_route_returns_created_script() -> None:
    script = make_script_data()
    use_case = CreateScriptStub(script)
    client = build_test_client(use_case)

    response = client.post(
        "/scripts",
        json={
            "name": "Deploy service",
            "content": "echo deploy",
            "execution_type": "local",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["id"] == str(script.id)
    assert use_case.arguments[1]["content"] == "echo deploy"


def test_post_script_route_validates_request_and_returns_conflict() -> None:
    client = build_test_client(CreateScriptStub(make_script_data()))
    invalid = client.post(
        "/scripts",
        json={"name": "", "content": "echo", "execution_type": "local"},
    )
    assert invalid.status_code == 422

    conflict_client = build_test_client(CreateScriptStub(make_script_data(), conflict=True))
    conflict = conflict_client.post(
        "/scripts",
        json={"name": "Deploy", "content": "echo", "execution_type": "local"},
    )
    assert conflict.status_code == 409

    unknown_field = build_test_client(CreateScriptStub(make_script_data())).post(
        "/scripts",
        json={
            "name": "Deploy",
            "content": "echo",
            "execution_type": "local",
            "unexpected": True,
        },
    )
    assert unknown_field.status_code == 422


def test_script_routes_reject_missing_identity() -> None:
    client = build_test_client(CreateScriptStub(make_script_data()), identity_error=True)

    response = client.get("/scripts")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_pending_execution_route_returns_script_payload_to_agent() -> None:
    script = make_script_data()
    now = datetime.now(UTC)
    execution = ScriptExecutionData(
        id=uuid4(),
        script_id=script.id,
        device_id=None,
        client_device_id=uuid4(),
        parameters=None,
        status=ExecutionStatus.PENDING,
        exit_code=None,
        started_at=None,
        finished_at=None,
        error_message=None,
        sanitized_output_summary=None,
        idempotency_key=None,
        created_at=now,
    )
    client_device_id = execution.client_device_id
    client = build_test_client(
        CreateScriptStub(script),
        pending_executions=GetPendingExecutionsStub([execution]),
        get_script=GetScriptStub(script),
    )

    response = client.get(f"/script-executions/pending?client_device_id={client_device_id}")

    assert response.status_code == 200
    item = response.json()["data"][0]
    assert item["execution"]["status"] == "pending"
    assert item["script"]["content"] == "echo deploy"
