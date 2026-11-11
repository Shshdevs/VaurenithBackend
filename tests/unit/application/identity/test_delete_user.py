from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.identity import UserNotFound
from app.application.identity.use_cases import DeleteUser


class FakeUserRepository:
    def __init__(self, deleted: bool) -> None:
        self.deleted = deleted
        self.deleted_user_id = None

    async def delete(self, user_id):
        self.deleted_user_id = user_id
        return self.deleted


@pytest.mark.anyio
async def test_delete_user_deletes_the_requested_account() -> None:
    user_id = uuid4()
    repository = FakeUserRepository(deleted=True)
    use_case = DeleteUser(repository, NoOpUnitOfWork())

    await use_case.execute(user_id)

    assert repository.deleted_user_id == user_id


@pytest.mark.anyio
async def test_delete_user_raises_not_found_for_missing_account() -> None:
    user_id = uuid4()
    use_case = DeleteUser(FakeUserRepository(deleted=False), NoOpUnitOfWork())

    with pytest.raises(UserNotFound):
        await use_case.execute(user_id)
