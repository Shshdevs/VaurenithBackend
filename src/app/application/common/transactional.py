from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar, cast

from app.application.common.unit_of_work import UnitOfWork

P = ParamSpec("P")
R = TypeVar("R")


class TransactionalUseCase(Protocol):
    _unit_of_work: UnitOfWork


def transactional[**P, R](
    method: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    @wraps(method)
    async def wrapped(self: TransactionalUseCase, *args: P.args, **kwargs: P.kwargs) -> R:
        async with self._unit_of_work.transaction():
            return await cast(Callable[..., Awaitable[R]], method)(self, *args, **kwargs)

    return cast(Callable[P, Awaitable[R]], wrapped)
