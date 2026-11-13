from types import TracebackType

import pytest

from app.bootstrap.dependencies import database as database_dependency


class AsyncContext:
    def __init__(self) -> None:
        self.exit_exception: type[BaseException] | None = None

    async def __aenter__(self) -> "AsyncContext":
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> bool:
        self.exit_exception = exception_type
        return False

    def begin(self) -> "AsyncContext":
        return self


@pytest.mark.anyio
async def test_database_session_rolls_back_and_closes_after_exception(monkeypatch) -> None:
    session_context = AsyncContext()
    transaction_context = AsyncContext()
    session_context.begin = transaction_context.begin
    monkeypatch.setattr(
        database_dependency,
        "SessionLocal",
        lambda: session_context,
    )
    dependency = database_dependency.get_database_session()

    await anext(dependency)
    with pytest.raises(RuntimeError, match="request failure"):
        await dependency.athrow(RuntimeError("request failure"))

    assert transaction_context.exit_exception is RuntimeError
    assert session_context.exit_exception is RuntimeError
