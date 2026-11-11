from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.exceptions import UserNotFound
from app.application.identity.interfaces import UserRepository


class DeleteUser:
    def __init__(self, user_repository: UserRepository, unit_of_work: UnitOfWork) -> None:
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, user_id: UUID) -> None:
        deleted = await self._user_repository.delete(user_id)
        if not deleted:
            raise UserNotFound(user_id)
