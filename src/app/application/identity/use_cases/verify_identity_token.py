from hashlib import sha256

from ....domain.identity.exceptions import InvalidEmail
from ....domain.identity.value_objects.email import EmailAddress
from ....domain.identity.value_objects.token_hash import TokenHash
from ..dto.verified_identity import VerifiedIdentity
from ..exceptions import InvalidIdentity
from ..interfaces.access_token_verifier import AccessTokenVerifier


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
