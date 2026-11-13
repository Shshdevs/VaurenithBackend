from datetime import UTC, datetime
from math import isfinite
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.application.identity.dto import IdentityTokenClaims
from app.application.identity.interfaces import AccessTokenVerifier


class JwtAccessTokenVerifier(AccessTokenVerifier):
    def __init__(
        self,
        public_key: str,
        issuer: str,
        audience: str,
        clock_skew_seconds: int,
        max_lifetime_seconds: int,
    ) -> None:
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience
        self._clock_skew_seconds = clock_skew_seconds
        self._max_lifetime_seconds = max_lifetime_seconds

    def verify(self, token: str) -> IdentityTokenClaims | None:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("typ") != "at+jwt":
                return None
            claims = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._clock_skew_seconds,
                options={
                    "require": [
                        "iss",
                        "aud",
                        "sub",
                        "exp",
                        "iat",
                        "nbf",
                        "jti",
                        "email",
                        "auth_provider",
                    ],
                },
            )
            if claims["iss"] != self._issuer or claims["aud"] != self._audience:
                return None
            if not all(
                isinstance(claims[name], (int, float))
                and not isinstance(claims[name], bool)
                and isfinite(claims[name])
                for name in ("iat", "nbf", "exp")
            ):
                return None
            if (
                claims["exp"] <= claims["iat"]
                or claims["exp"] - claims["iat"] > self._max_lifetime_seconds
            ):
                return None
            if not isinstance(claims["sub"], str):
                return None
            user_id = UUID(claims["sub"])
            email = claims["email"]
            auth_provider = claims["auth_provider"]
            expires_at = datetime.fromtimestamp(claims["exp"], UTC)
            jti = claims["jti"]
            UUID(jti)
        except (InvalidTokenError, KeyError, TypeError, ValueError, OverflowError):
            return None

        if (
            not isinstance(email, str)
            or not isinstance(auth_provider, str)
            or not auth_provider
            or len(auth_provider) > 100
            or not isinstance(jti, str)
            or not jti
            or len(jti) > 255
        ):
            return None

        return IdentityTokenClaims(
            user_id=user_id,
            email=email,
            auth_provider=auth_provider,
            expires_at=expires_at,
        )
