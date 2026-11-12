from datetime import UTC, datetime

from app.application.identity.dto import VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.application.identity.interfaces import SessionRepository
from app.application.identity.use_cases.verify_identity_token import VerifyIdentityToken


class AuthenticateIdentity:
    def __init__(
        self,
        verify_identity_token: VerifyIdentityToken,
        session_repository: SessionRepository,
    ) -> None:
        self._verify_identity_token = verify_identity_token
        self._session_repository = session_repository

    async def execute(self, token: str) -> VerifiedIdentity:
        identity = self._verify_identity_token.execute(token)
        if not await self._session_repository.has_active_session(
            identity.user_id,
            identity.token_hash,
            datetime.now(UTC),
        ):
            raise InvalidIdentity("Identity session is inactive")
        return identity
