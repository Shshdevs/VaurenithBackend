from enum import StrEnum
from http import HTTPStatus

from app.api.schemas.common import Schema
from app.domain.common.enums import EntityType


class ResponseCode(StrEnum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    STATUS_UPDATED = "STATUS_UPDATED"
    DELETED = "DELETED"
    RETRIEVED = "RETRIEVED"
    RECORDED = "RECORDED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INFORMATIONAL = "INFORMATIONAL"
    WARNING = "WARNING"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CACHED = "CACHED"
    LOGGED_IN = "LOGGED_IN"
    LOGGED_OUT = "LOGGED_OUT"
    SYNCED = "SYNCED"
    RESYNC_REQUIRED = "RESYNC_REQUIRED"
    OK = "OK"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INVALID_INPUT = "INVALID_INPUT"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def format_http_status(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "Unknown Status"
    return f"{status_code} {phrase}"


class ApiResponse[T](Schema):
    status: str
    code: ResponseCode
    entity_type: EntityType | None
    data: T | None = None
    details: object | None = None
