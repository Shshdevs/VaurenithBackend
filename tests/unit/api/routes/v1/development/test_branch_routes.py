from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.branch.conftest import (
    BranchRepositoryStub,
    RepositoryRepositoryStub,
)

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.development.branch import build_branch_router
from app.application.development import (
    CreateBranch,
    DeleteBranch,
    GetBranch,
    GetRepositoryBranches,
    UpdateBranch,
)
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_client():
    user_id = uuid4()
    repository_id = uuid4()
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="branch-api-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    branch_repository = BranchRepositoryStub(user_id, {repository_id})
    repository_repository = RepositoryRepositoryStub({repository_id})
    unit_of_work = NoOpUnitOfWork()
    create = CreateBranch(branch_repository, repository_repository, unit_of_work)
    get = GetBranch(branch_repository)
    list_branches = GetRepositoryBranches(branch_repository, repository_repository)
    update = UpdateBranch(branch_repository, unit_of_work)
    delete = DeleteBranch(branch_repository, unit_of_work)
    router = build_branch_router(
        create_branch_dependency=lambda: create,
        get_branch_dependency=lambda: get,
        get_repository_branches_dependency=lambda: list_branches,
        update_branch_dependency=lambda: update,
        delete_branch_dependency=lambda: delete,
        authenticated_identity_dependency=lambda: identity,
    )
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    register_error_handlers(app)
    return TestClient(app), repository_id


def test_branch_api_supports_create_list_get_update_and_delete() -> None:
    client, repository_id = make_client()
    payload = {
        "name": "main",
        "commit_hash": "a" * 40,
        "is_remote": False,
        "is_current": True,
        "last_updated_at": "2026-11-12T10:00:00Z",
        "last_synced_at": "2026-11-12T10:00:00Z",
    }

    created_response = client.post(
        f"/v1/repositories/{repository_id}/branches", json=payload
    )
    assert created_response.status_code == 201
    created = created_response.json()["data"]
    branch_id = created["id"]

    listed_response = client.get(f"/v1/repositories/{repository_id}/branches")
    assert listed_response.status_code == 200
    assert [branch["id"] for branch in listed_response.json()["data"]] == [branch_id]

    fetched_response = client.get(f"/v1/branches/{branch_id}")
    assert fetched_response.status_code == 200
    assert fetched_response.json()["data"] == created

    updated_response = client.put(
        f"/v1/branches/{branch_id}",
        json={**payload, "name": "main-renamed", "is_current": False},
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["data"]["name"] == "main-renamed"

    deleted_response = client.delete(f"/v1/branches/{branch_id}")
    assert deleted_response.status_code == 200
    assert client.get(f"/v1/branches/{branch_id}").status_code == 404


def test_branch_api_validates_payload_and_reports_duplicate() -> None:
    client, repository_id = make_client()
    response = client.post(
        f"/v1/repositories/{repository_id}/branches",
        json={"name": "", "commit_hash": "a" * 40},
    )
    assert response.status_code == 422

    payload = {"name": "main", "is_remote": False}
    assert (
        client.post(f"/v1/repositories/{repository_id}/branches", json=payload).status_code
        == 201
    )
    duplicate = client.post(f"/v1/repositories/{repository_id}/branches", json=payload)
    assert duplicate.status_code == 409
