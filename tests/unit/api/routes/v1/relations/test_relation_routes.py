from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpUnitOfWork
from tests.unit.application.relations.test_relation_use_cases import (
    RelationRepositoryStub,
)

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.relations.relation import build_relation_router
from app.application.identity import VerifiedIdentity
from app.application.relations import (
    CreateRelation,
    DeleteRelation,
    GetProjectRelations,
    GetRelation,
    UpdateRelation,
)
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash


def make_client():
    user_id = uuid4()
    project_id = uuid4()
    source_entity_id = project_id
    target_entity_id = uuid4()
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="relation-api-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    repository = RelationRepositoryStub(user_id, project_id)
    source = (EntityType.PROJECT, source_entity_id)
    target = (EntityType.OTHER, target_entity_id)
    repository.references.update({source, target})
    unit_of_work = NoOpUnitOfWork()
    create = CreateRelation(repository, unit_of_work)
    get = GetRelation(repository)
    list_relations = GetProjectRelations(repository)
    update = UpdateRelation(repository, unit_of_work)
    delete = DeleteRelation(repository, unit_of_work)
    router = build_relation_router(
        create_relation_dependency=lambda: create,
        get_relation_dependency=lambda: get,
        get_project_relations_dependency=lambda: list_relations,
        update_relation_dependency=lambda: update,
        delete_relation_dependency=lambda: delete,
        authenticated_identity_dependency=lambda: identity,
    )
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    register_error_handlers(app)
    return TestClient(app), project_id, source_entity_id, target_entity_id


def test_relation_api_supports_create_list_get_update_and_delete() -> None:
    client, project_id, source_id, target_id = make_client()
    path = f"/v1/projects/{project_id}/relations"
    payload = {
        "source_entity_type": "project",
        "source_entity_id": str(source_id),
        "target_entity_type": "other",
        "target_entity_id": str(target_id),
        "relation_type": "contains",
        "confidence": "0.7500",
        "metadata": {"source": "api-test"},
    }

    created_response = client.post(path, json=payload)
    assert created_response.status_code == 201
    created = created_response.json()["data"]
    relation_id = created["id"]
    assert created["origin"] == "user_defined"

    listed = client.get(path)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [relation_id]
    filtered = client.get(
        path,
        params={"entity_type": "other", "entity_id": str(target_id)},
    )
    assert [item["id"] for item in filtered.json()["data"]] == [relation_id]

    relation_path = f"{path}/{relation_id}"
    fetched = client.get(relation_path)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == relation_id

    updated_payload = {**payload, "relation_type": "references"}
    updated = client.put(relation_path, json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["data"]["relation_type"] == "references"

    deleted = client.delete(relation_path)
    assert deleted.status_code == 200
    assert client.get(relation_path).status_code == 404


def test_relation_api_rejects_unknown_references_and_incomplete_filters() -> None:
    client, project_id, source_id, _ = make_client()
    path = f"/v1/projects/{project_id}/relations"
    response = client.post(
        path,
        json={
            "source_entity_type": "project",
            "source_entity_id": str(source_id),
            "target_entity_type": "device",
            "target_entity_id": str(uuid4()),
            "relation_type": "contains",
        },
    )
    assert response.status_code == 404
    assert client.get(path, params={"entity_type": "project"}).status_code == 422
