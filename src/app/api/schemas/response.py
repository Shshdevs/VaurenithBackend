from http import HTTPStatus

from app.api.schemas.common import Schema


def format_http_status(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "Unknown Status"
    return f"{status_code} {phrase}"


class ApiResponse[T](Schema):
    status: str
    message: str | None = None
    data: T | None = None
