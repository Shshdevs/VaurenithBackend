from datetime import UTC, datetime
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from ....application.identity.dto import IdentityTokenClaims
from ....application.identity.interfaces import AccessTokenVerifier


class JwtAccessTokenVerifier(AccessTokenVerifier):
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def verify(self, token: str) -> IdentityTokenClaims | None:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "email", "auth_provider"]},
            )
            user_id = UUID(claims["sub"])
            email = claims["email"]
            auth_provider = claims["auth_provider"]
            expires_at = datetime.fromtimestamp(claims["exp"], UTC)
        except (InvalidTokenError, KeyError, TypeError, ValueError, OverflowError):
            return None

        if (
            not isinstance(email, str)
            or not isinstance(auth_provider, str)
            or not auth_provider
            or len(auth_provider) > 100
        ):
            return None

        return IdentityTokenClaims(
            user_id=user_id,
            email=email,
            auth_provider=auth_provider,
            expires_at=expires_at,
        )
