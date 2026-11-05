from http import HTTPStatus

from .common import Schema


def format_http_status(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "Unknown Status"
    return f"{status_code} {phrase}"


class ApiResponse[T](Schema):
    message: str
    status: str
    data: T | None = None
