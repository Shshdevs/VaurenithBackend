from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.middleware.error_handler import register_error_handlers
from app.api.schemas.common import Schema


class NestedRequest(Schema):
    count: int


class ValidationRequest(Schema):
    count: int
    nested: NestedRequest


def build_test_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/validation")
    async def validate_request(request: ValidationRequest) -> dict[str, str]:
        return {"result": "accepted"}

    return TestClient(app)


def test_validation_error_does_not_echo_unknown_field_value() -> None:
    secret = "sensitive-unknown-field-value"
    response = build_test_client().post(
        "/validation",
        json={"count": 1, "nested": {"count": 2}, "api_token": secret},
    )

    assert response.status_code == 422
    assert secret not in response.text
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "entity_type": None,
        "status": "422 Unprocessable Content",
        "data": [
            {
                "loc": ["body", "api_token"],
                "type": "extra_forbidden",
                "msg": "Extra inputs are not permitted",
            }
        ],
        "details": None,
    }


def test_validation_error_does_not_echo_invalid_type_value() -> None:
    secret = "sensitive-invalid-type-value"
    response = build_test_client().post(
        "/validation",
        json={"count": secret, "nested": {"count": 2}},
    )

    assert response.status_code == 422
    assert secret not in response.text
    error = response.json()["data"][0]
    assert error["loc"] == ["body", "count"]
    assert error["type"] == "int_parsing"
    assert "valid integer" in error["msg"]
    assert set(error) == {"loc", "type", "msg"}


def test_nested_validation_error_does_not_echo_body_values() -> None:
    secret = "sensitive-nested-value"
    response = build_test_client().post(
        "/validation",
        json={"count": 1, "nested": {"count": secret}},
    )

    assert response.status_code == 422
    assert secret not in response.text
    error = response.json()["data"][0]
    assert error["loc"] == ["body", "nested", "count"]
    assert error["type"] == "int_parsing"
    assert "valid integer" in error["msg"]
    assert set(error) == {"loc", "type", "msg"}


def test_database_connection_error_returns_generic_service_unavailable() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/database")
    async def database_failure() -> None:
        raise OperationalError("SELECT 1", {}, RuntimeError("private database detail"))

    response = TestClient(app).get("/database")

    assert response.status_code == 503
    assert "private database detail" not in response.text
    assert response.json() == {
        "code": "UNAVAILABLE",
        "entity_type": None,
        "status": "503 Service Unavailable",
        "data": None,
        "details": None,
    }
