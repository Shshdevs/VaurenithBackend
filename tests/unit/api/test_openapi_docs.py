from fastapi.testclient import TestClient

from app.main import create_app


def test_redoc_lists_commit_routes_in_development_group() -> None:
    client = TestClient(create_app())

    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    schema = openapi_response.json()
    commit_paths = [path for path in schema["paths"] if "/commits" in path]
    assert commit_paths
    operations = [
        operation for path in commit_paths for operation in schema["paths"][path].values()
    ]
    assert all("commits" in operation["tags"] for operation in operations)
    development_group = next(
        group for group in schema["x-tagGroups"] if group["name"] == "development"
    )
    assert "commits" in development_group["tags"]
    branch_paths = [path for path in schema["paths"] if "/branches" in path]
    assert branch_paths
    branch_operations = [
        operation for path in branch_paths for operation in schema["paths"][path].values()
    ]
    assert all("branches" in operation["tags"] for operation in branch_operations)
    assert "branches" in development_group["tags"]


def test_redoc_lists_relation_routes_in_relations_group() -> None:
    client = TestClient(create_app())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    relation_paths = [path for path in schema["paths"] if "/relations" in path]
    assert relation_paths
    operations = [
        operation for path in relation_paths for operation in schema["paths"][path].values()
    ]
    assert all("relations" in operation["tags"] for operation in operations)
    relation_group = next(
        group for group in schema["x-tagGroups"] if group["name"] == "relations"
    )
    assert relation_group["tags"] == ["relations"]
