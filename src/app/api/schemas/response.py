from app.api.schemas.common import Schema


class ApiResponse[T](Schema):
    message: str
    data: T | None = None
