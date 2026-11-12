from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.v1.automation import build_automation_router
from app.api.routes.v1.synchronization.change_log import build_change_log_route
from app.application.automation.use_cases.scripts import (
    CreateScript,
    DeleteScript,
    UpdateScript,
)
from app.application.identity import VerifiedIdentity
from app.application.synchronization.use_cases.change_log import GetUserChangeLog
from app.domain.automation import Script
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.synchronization import ChangeLog, ChangeOperation


class MemoryScriptRepository:
    def __init__(self) -> None:
        self.scripts: dict[UUID, Script] = {}

    async def get_script(self, user_id: UUID, script_id: UUID) -> Script | None:
        return self.scripts.get(script_id)

    async def get_scripts(self, user_id: UUID) -> list[Script]:
        return list(self.scripts.values())

    async def create_script(self, user_id: UUID, script: Script) -> None:
        self.scripts[script.id] = script

    async def update_script(
        self, user_id: UUID, script: Script, expected_version: int
    ) -> bool:
        current = self.scripts.get(script.id)
        if current is None or current.version != expected_version:
            return False
        self.scripts[script.id] = script
        return True

    async def delete_script(
        self, user_id: UUID, script_id: UUID, expected_version: int
    ) -> bool:
        script = self.scripts.get(script_id)
        if script is None or script.version != expected_version:
            return False
        del self.scripts[script_id]
        return True


class MemoryProjectRepository:
    async def get_by_id(self, user_id: UUID, project_id: UUID) -> None:
        return None


class MemoryChangeLogRepository:
    def __init__(self) -> None:
        self.changes: list[ChangeLog] = []

    async def execute(
        self,
        identity: VerifiedIdentity,
        entity_type: EntityType,
        entity_id: UUID,
        operation: ChangeOperation,
        version: int,
        payload: dict | None = None,
    ) -> None:
        await self.create(
            ChangeLog(
                change_log_id=uuid4(),
                user_id=identity.user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                operation=operation,
                version=version,
                changed_by_user_id=identity.user_id,
                created_at=datetime.now(UTC),
                payload=payload,
            )
        )

    async def create(self, change: ChangeLog) -> None:
        self.changes.append(
            ChangeLog(
                change_log_id=change.id,
                user_id=change.user_id,
                entity_type=change.entity_type,
                entity_id=change.entity_id,
                operation=change.operation,
                version=change.version,
                changed_by_user_id=change.changed_by_user_id,
                changed_by_client_id=change.changed_by_client_id,
                created_at=change.created_at,
                payload=change.payload,
                sequence=len(self.changes) + 1,
            )
        )

    async def get_by_user(
        self, user_id: UUID, after_sequence: int = 0, limit: int = 100
    ) -> list[ChangeLog]:
        return [
            change
            for change in self.changes
            if change.user_id == user_id
            and change.sequence is not None
            and change.sequence > after_sequence
        ][:limit]


class NoOpUnitOfWork:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    def transaction(self) -> NoOpUnitOfWork:
        return self


def build_client() -> tuple[TestClient, MemoryScriptRepository]:
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("script-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )
    scripts = MemoryScriptRepository()
    change_logs = MemoryChangeLogRepository()
    projects = MemoryProjectRepository()
    unit_of_work = NoOpUnitOfWork()

    def unused_dependency() -> None:
        return None

    def provide_create_script() -> CreateScript:
        return CreateScript(scripts, projects, change_logs, unit_of_work)

    def provide_update_script() -> UpdateScript:
        return UpdateScript(scripts, projects, change_logs, unit_of_work)

    def provide_delete_script() -> DeleteScript:
        return DeleteScript(scripts, projects, change_logs, unit_of_work)

    def provide_change_log() -> GetUserChangeLog:
        return GetUserChangeLog(change_logs)

    def provide_identity() -> VerifiedIdentity:
        return identity

    app = FastAPI()
    app.include_router(
        build_automation_router(
            create_automation_script_dependency=provide_create_script,
            get_automation_script_dependency=unused_dependency,
            get_user_automation_scripts_dependency=unused_dependency,
            update_automation_script_dependency=provide_update_script,
            delete_automation_script_dependency=provide_delete_script,
            add_automation_script_target_dependency=unused_dependency,
            get_automation_script_targets_dependency=unused_dependency,
            remove_automation_script_target_dependency=unused_dependency,
            request_automation_script_execution_dependency=unused_dependency,
            get_pending_automation_script_executions_dependency=unused_dependency,
            get_automation_script_execution_dependency=unused_dependency,
            get_automation_script_executions_dependency=unused_dependency,
            start_automation_script_execution_dependency=unused_dependency,
            report_automation_script_execution_result_dependency=unused_dependency,
            authenticated_identity_dependency=provide_identity,
        )
    )
    app.include_router(build_change_log_route(provide_change_log, provide_identity))
    return TestClient(app), scripts


def test_script_crud_change_logs_expose_only_allowlisted_metadata() -> None:
    client, scripts = build_client()
    markers = [
        "SCRIPT_CONTENT_SECRET_CREATE",
        "SCRIPT_CONTENT_SECRET_UPDATE",
        "SCRIPT_PARAMETER_SECRET_CREATE",
        "SCRIPT_PARAMETER_SECRET_UPDATE",
        "SCRIPT_DESCRIPTION_SECRET",
        "SCRIPT_INTERPRETER_SECRET",
        "SCRIPT_NAME_SECRET",
    ]
    create_response = client.post(
        "/scripts",
        json={
            "name": markers[6],
            "description": markers[4],
            "content": markers[0],
            "interpreter": markers[5],
            "execution_type": "local",
            "parameters": {"environment": {"ACCESS_KEY": markers[2]}},
            "risk_level": "moderate",
            "requires_confirmation": True,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["data"]["content"] == markers[0]
    script_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/scripts/{script_id}",
        json={
            "version": 1,
            "name": "Updated script",
            "description": markers[4],
            "content": markers[1],
            "interpreter": markers[5],
            "execution_type": "ssh",
            "parameters": {"nested": [{"env": {"TOKEN": markers[3]}}]},
            "risk_level": "dangerous",
            "requires_confirmation": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["content"] == markers[1]

    sync_response = client.get("/change-logs?after_sequence=0&limit=100")
    assert sync_response.status_code == 200
    serialized_response = json.dumps(sync_response.json())
    assert all(marker not in serialized_response for marker in markers)
    changes = sync_response.json()["data"]
    assert [
        (change["entity_type"], change["operation"], change["version"], change["sequence"])
        for change in changes
    ] == [("script", "insert", 1, 1), ("script", "update", 2, 2)]
    assert changes[0]["payload"] == {
        "project_id": None,
        "execution_type": "local",
        "risk_level": "moderate",
        "requires_confirmation": True,
    }
    assert changes[1]["payload"] == {
        "project_id": None,
        "execution_type": "ssh",
        "risk_level": "dangerous",
        "requires_confirmation": True,
    }

    delete_response = client.delete(f"/scripts/{script_id}?expected_version=2")
    assert delete_response.status_code == 200
    delete_sync_response = client.get("/change-logs?after_sequence=2&limit=100")
    assert delete_sync_response.status_code == 200
    delete_change = delete_sync_response.json()["data"][0]
    assert (
        delete_change["operation"],
        delete_change["version"],
        delete_change["sequence"],
    ) == (
        "delete",
        3,
        3,
    )
    assert delete_change["payload"] is None
    assert scripts.scripts == {}
