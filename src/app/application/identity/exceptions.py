from uuid import UUID

from ..common.exceptions import Conflict, NotFound, Unauthorized


class UserNotFound(NotFound):
    def __init__(self, user_id: UUID) -> None:
        super().__init__(f'UserNotFound: user with id "{user_id}" not found')


class UserAlreadyExists(Conflict):
    def __init__(self, email: str) -> None:
        super().__init__(f'UserAlreadyExists: user with email "{email}" already exists')


class InvalidIdentity(Unauthorized):
    def __init__(self, message: str = "Identity token is invalid") -> None:
        super().__init__(message)
