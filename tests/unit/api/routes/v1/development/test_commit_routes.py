from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.commit.conftest import (
    CommitRepositoryStub,
    RepositoryRepositoryStub,
)

from app.api.routes.v1.development.commit import build_commit_router
from app.application.development import CreateCommit, GetCommit, GetRepositoryCommits
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_client():
    user_id = uuid4()
    repository_id = uuid4()
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="commit-api-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    commit_repository = CommitRepositoryStub(user_id, {repository_id})
    repository_repository = RepositoryRepositoryStub({repository_id})
    create = CreateCommit(commit_repository, repository_repository, NoOpUnitOfWork())
    get = GetCommit(commit_repository)
    list_commits = GetRepositoryCommits(commit_repository, repository_repository)
    router = build_commit_router(
        create_commit_dependency=lambda: create,
        get_commit_dependency=lambda: get,
        get_repository_commits_dependency=lambda: list_commits,
        authenticated_identity_dependency=lambda: identity,
    )
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return TestClient(app), repository_id


def test_commit_api_supports_cache_list_and_get() -> None:
    client, repository_id = make_client()
    response = client.post(
        f"/v1/repositories/{repository_id}/commits",
        json={
            "hash": "a" * 40,
            "author_name": "Ada Lovelace",
            "author_email": "ada@example.test",
            "message": "Initial commit",
            "committed_at": "2026-11-12T10:00:00Z",
            "changed_files": ["src/main.py"],
        },
    )

    assert response.status_code == 201
    created = response.json()["data"]
    assert created["cached_at"] is not None
    assert created["hash"] == "a" * 40

    listed = client.get(f"/v1/repositories/{repository_id}/commits")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [created["id"]]

    fetched = client.get(f"/v1/commits/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"] == created


def test_commit_api_validates_hash_and_timestamp() -> None:
    client, repository_id = make_client()
    response = client.post(
        f"/v1/repositories/{repository_id}/commits",
        json={"hash": "invalid"},
    )
    assert response.status_code == 422

    response = client.post(
        f"/v1/repositories/{repository_id}/commits",
        json={"hash": "a" * 40, "committed_at": "not-a-date"},
    )
    assert response.status_code == 422
