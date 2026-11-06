from hashlib import sha256

from app.application.identity.dto import VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.application.identity.interfaces import AccessTokenVerifier
from app.domain.identity import EmailAddress, InvalidEmail, TokenHash


class VerifyIdentityToken:
    def __init__(self, token_verifier: AccessTokenVerifier) -> None:
        self._token_verifier = token_verifier

    def execute(self, token: str) -> VerifiedIdentity:
        claims = self._token_verifier.verify(token)
        if claims is None:
            raise InvalidIdentity()
        try:
            email = EmailAddress(claims.email)
        except InvalidEmail as error:
            raise InvalidIdentity() from error
        return VerifiedIdentity(
            user_id=claims.user_id,
            email=email,
            auth_provider=claims.auth_provider,
            expires_at=claims.expires_at,
            token_hash=TokenHash(sha256(token.encode()).hexdigest()),
        )
