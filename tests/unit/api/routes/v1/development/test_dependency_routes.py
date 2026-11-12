from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.dependency.conftest import (
    CodeComponentRepositoryStub,
    DependencyRepositoryStub,
    RepositoryRepositoryStub,
    make_component,
)

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.development.dependency import build_dependency_router
from app.application.development import (
    CreateDependency,
    DeleteDependency,
    GetComponentDependencies,
    GetDependency,
    GetRepositoryDependencies,
    UpdateDependency,
)
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_client():
    user_id = uuid4()
    repository_id = uuid4()
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="dependency-api-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    components = CodeComponentRepositoryStub(user_id)
    source = make_component(repository_id, name="source.py")
    target = make_component(repository_id, name="target.py")
    components.components[source.id] = source
    components.components[target.id] = target
    repositories = RepositoryRepositoryStub({repository_id})
    dependencies = DependencyRepositoryStub(user_id, components)
    unit_of_work = NoOpUnitOfWork()
    create = CreateDependency(dependencies, components, repositories, unit_of_work)
    get = GetDependency(dependencies)
    get_component = GetComponentDependencies(dependencies, components)
    get_repository = GetRepositoryDependencies(dependencies, repositories)
    update = UpdateDependency(dependencies, components, unit_of_work)
    delete = DeleteDependency(dependencies, unit_of_work)
    router = build_dependency_router(
        create_dependency_dependency=lambda: create,
        get_dependency_dependency=lambda: get,
        get_component_dependencies_dependency=lambda: get_component,
        get_repository_dependencies_dependency=lambda: get_repository,
        update_dependency_dependency=lambda: update,
        delete_dependency_dependency=lambda: delete,
        authenticated_identity_dependency=lambda: identity,
    )
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    register_error_handlers(app)
    return TestClient(app), repository_id, source.id, target.id


def make_payload(source_component_id, target_component_id):
    return {
        "source_component_id": str(source_component_id),
        "target_component_id": str(target_component_id),
        "dependency_type": "import",
        "is_directed": True,
        "source_type": "user_defined",
        "confidence": "0.8750",
        "analysis_version": "1.0",
        "analyzed_at": "2026-11-12T10:00:00Z",
        "metadata": {"module": "target"},
    }


def test_dependency_api_supports_create_list_get_update_and_delete() -> None:
    client, repository_id, source_id, target_id = make_client()
    created_response = client.post(
        f"/v1/repositories/{repository_id}/dependencies",
        json=make_payload(source_id, target_id),
    )

    assert created_response.status_code == 201
    created = created_response.json()["data"]
    dependency_id = created["id"]

    repository_list = client.get(f"/v1/repositories/{repository_id}/dependencies")
    assert repository_list.status_code == 200
    assert [item["id"] for item in repository_list.json()["data"]] == [dependency_id]

    component_list = client.get(f"/v1/code-components/{source_id}/dependencies")
    assert component_list.status_code == 200
    assert [item["id"] for item in component_list.json()["data"]] == [dependency_id]

    fetched = client.get(f"/v1/dependencies/{dependency_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"] == created

    updated = client.put(
        f"/v1/dependencies/{dependency_id}",
        json={
            **make_payload(target_id, source_id),
            "dependency_type": "reference",
            "is_directed": False,
            "metadata": {"reviewed": True},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["dependency_type"] == "reference"
    assert updated.json()["data"]["is_directed"] is False
    assert updated.json()["data"]["metadata"] == {"reviewed": True}

    deleted = client.delete(f"/v1/dependencies/{dependency_id}")
    assert deleted.status_code == 200
    assert client.get(f"/v1/dependencies/{dependency_id}").status_code == 404


def test_dependency_api_validates_confidence_and_duplicate_edges() -> None:
    client, repository_id, source_id, target_id = make_client()
    payload = make_payload(source_id, target_id)
    invalid = client.post(
        f"/v1/repositories/{repository_id}/dependencies",
        json={**payload, "confidence": "1.0001"},
    )
    assert invalid.status_code == 422

    assert (
        client.post(
            f"/v1/repositories/{repository_id}/dependencies", json=payload
        ).status_code
        == 201
    )
    duplicate = client.post(f"/v1/repositories/{repository_id}/dependencies", json=payload)
    assert duplicate.status_code == 409
