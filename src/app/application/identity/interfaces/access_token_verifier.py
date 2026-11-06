from typing import Protocol

from app.application.identity.dto.identity_token_claims import IdentityTokenClaims


class AccessTokenVerifier(Protocol):
    def verify(self, token: str) -> IdentityTokenClaims | None: ...
