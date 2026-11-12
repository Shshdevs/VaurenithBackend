from collections.abc import Iterable

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.middleware.request_body_limit import RequestBodyLimitMiddleware


def build_client(limit: int = 8) -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestBodyLimitMiddleware, max_body_size=limit)
    register_error_handlers(app)

    @app.post("/body")
    async def read_body(request: Request) -> dict[str, int]:
        return {"size": len(await request.body())}

    return TestClient(app)


def test_request_within_limit_is_accepted() -> None:
    response = build_client().post("/body", content=b"1234567")

    assert response.status_code == 200
    assert response.json() == {"size": 7}


def test_request_at_limit_is_accepted() -> None:
    response = build_client().post("/body", content=b"12345678")

    assert response.status_code == 200
    assert response.json() == {"size": 8}


def test_request_over_limit_returns_standard_413_without_body_reflection() -> None:
    secret = b"sensitive-body-marker"
    response = build_client().post("/body", content=secret)

    assert response.status_code == 413
    assert response.json() == {
        "code": "HTTP_ERROR",
        "entity_type": None,
        "status": "413 Content Too Large",
        "data": None,
        "details": "Request body exceeds the maximum allowed size",
    }
    assert secret.decode() not in response.text


def test_invalid_and_missing_content_length_are_checked_by_actual_bytes() -> None:
    client = build_client()
    invalid_length = client.post(
        "/body", content=b"123456789", headers={"Content-Length": "invalid"}
    )
    missing_length = client.post("/body", content=b"123456789")

    assert invalid_length.status_code == 413
    assert missing_length.status_code == 413


def test_streamed_body_is_counted_across_chunks() -> None:
    def chunks() -> Iterable[bytes]:
        yield b"1234"
        yield b"5678"
        yield b"9"

    response = build_client().post("/body", content=chunks())

    assert response.status_code == 413


def test_mismatched_content_length_does_not_bypass_actual_size_check() -> None:
    response = build_client().post(
        "/body", content=b"123456789", headers={"Content-Length": "1"}
    )

    assert response.status_code == 413


def test_normal_endpoint_behavior_is_preserved() -> None:
    response = build_client(limit=64).post("/body", json={"ok": True})

    assert response.status_code == 200
    assert response.json()["size"] > 0
