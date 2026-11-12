import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.schemas import ApiResponse, ResponseCode, format_http_status


class RequestBodyTooLarge(Exception):
    pass


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_size: int) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        content_lengths = [
            value.strip() for name, value in headers if name.lower() == b"content-length"
        ]
        declared_size = self._content_length(content_lengths)
        if declared_size is not None and declared_size > self.max_body_size:
            await self._reject(send)
            return

        received_size = 0
        rejected = False

        async def limited_receive() -> Message:
            nonlocal received_size, rejected
            message = await receive()
            if message["type"] == "http.request":
                received_size += len(message.get("body", b""))
                if received_size > self.max_body_size:
                    rejected = True
                    raise RequestBodyTooLarge
            return message

        async def guarded_send(message: Message) -> None:
            if rejected:
                return
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except RequestBodyTooLarge:
            rejected = True
        if rejected:
            await self._reject(send)

    @staticmethod
    def _content_length(values: list[bytes]) -> int | None:
        if not values:
            return None
        try:
            parsed = [int(value, 10) for value in values]
        except ValueError:
            return None
        if any(value < 0 for value in parsed) or len(set(parsed)) != 1:
            return None
        return parsed[0]

    async def _reject(self, send: Send) -> None:
        body = ApiResponse[dict[str, str]](
            code=ResponseCode.HTTP_ERROR,
            entity_type=None,
            status=format_http_status(413),
            details="Request body exceeds the maximum allowed size",
        )
        encoded = json.dumps(body.model_dump(mode="json")).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(encoded)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": encoded})
