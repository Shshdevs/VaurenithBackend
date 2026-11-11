from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.code_component.conftest import (
    ChangeRecorderStub,
    CodeComponentRepositoryStub,
    RepositoryRepositoryStub,
)

from app.api.routes.v1.development.code_component import build_code_component_router
from app.application.development import (
    CreateCodeComponent,
    DeleteCodeComponent,
    GetCodeComponent,
    GetRepositoryCodeComponents,
    UpdateCodeComponent,
)
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_client():
    user_id = uuid4()
    repository_id = uuid4()
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="code-component-api-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    component_repository = CodeComponentRepositoryStub(user_id, {repository_id})
    repository_repository = RepositoryRepositoryStub({repository_id})
    recorder = ChangeRecorderStub()
    unit_of_work = NoOpUnitOfWork()
    create = CreateCodeComponent(
        component_repository, repository_repository, recorder, unit_of_work
    )
    get = GetCodeComponent(component_repository)
    list_components = GetRepositoryCodeComponents(
        component_repository, repository_repository
    )
    update = UpdateCodeComponent(component_repository, recorder, unit_of_work)
    delete = DeleteCodeComponent(component_repository, recorder, unit_of_work)
    router = build_code_component_router(
        create_code_component_dependency=lambda: create,
        get_code_component_dependency=lambda: get,
        get_repository_code_components_dependency=lambda: list_components,
        update_code_component_dependency=lambda: update,
        delete_code_component_dependency=lambda: delete,
        authenticated_identity_dependency=lambda: identity,
    )
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return TestClient(app), repository_id


def test_code_component_api_supports_create_list_update_get_and_delete() -> None:
    client, repository_id = make_client()
    payload = {
        "name": "main.py",
        "path": "src/main.py",
        "component_type": "file",
        "language": "python",
        "symbol": "main",
        "start_line": 1,
        "end_line": 20,
        "analysis_version": "1.0",
        "source_commit_hash": "a" * 40,
    }

    created_response = client.post(
        f"/v1/repositories/{repository_id}/code-components", json=payload
    )
    assert created_response.status_code == 201
    created = created_response.json()["data"]
    component_id = created["id"]
    assert created["version"] == 1

    listed_response = client.get(f"/v1/repositories/{repository_id}/code-components")
    assert listed_response.status_code == 200
    assert [item["id"] for item in listed_response.json()["data"]] == [component_id]

    updated_response = client.put(
        f"/v1/code-components/{component_id}",
        json={**payload, "name": "app.py", "version": 1},
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["data"]["name"] == "app.py"
    assert updated_response.json()["data"]["version"] == 2

    fetched_response = client.get(f"/v1/code-components/{component_id}")
    assert fetched_response.status_code == 200
    assert fetched_response.json()["data"]["name"] == "app.py"

    deleted_response = client.delete(
        f"/v1/code-components/{component_id}", params={"expected_version": 2}
    )
    assert deleted_response.status_code == 200


def test_code_component_api_validates_payload_and_expected_version() -> None:
    client, repository_id = make_client()
    response = client.post(
        f"/v1/repositories/{repository_id}/code-components",
        json={"name": "", "path": "", "component_type": "invalid"},
    )
    assert response.status_code == 422
    response = client.delete(f"/v1/code-components/{uuid4()}")
    assert response.status_code == 422
