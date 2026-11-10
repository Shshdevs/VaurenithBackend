from datetime import UTC, datetime

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.application.identity.interfaces import SessionRepository


class RevokeSession:
    def __init__(
        self,
        session_repository: SessionRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._session_repository = session_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity) -> None:
        revoked = await self._session_repository.revoke_session(
            identity.token_hash,
            datetime.now(UTC),
        )
        if not revoked:
            raise InvalidIdentity("Identity session is inactive")
