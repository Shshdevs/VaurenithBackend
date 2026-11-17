import logging
from datetime import UTC, datetime
from math import isfinite
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.application.identity.dto import IdentityTokenClaims
from app.application.identity.interfaces import AccessTokenVerifier

logger = logging.getLogger(__name__)


class JwtAccessTokenVerifier(AccessTokenVerifier):
    def __init__(
        self,
        public_key: str,
        issuer: str,
        audience: str,
        clock_skew_seconds: int,
        max_lifetime_seconds: int,
        public_key_path: str = "unset",
    ) -> None:
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience
        self._clock_skew_seconds = clock_skew_seconds
        self._max_lifetime_seconds = max_lifetime_seconds
        logger.info(
            "jwt_verifier_config issuer=%s audience=%s public_key_path=%s "
            "max_lifetime_seconds=%s clock_skew_seconds=%s",
            issuer,
            audience,
            public_key_path,
            max_lifetime_seconds,
            clock_skew_seconds,
        )

    def verify(self, token: str) -> IdentityTokenClaims | None:
        checks: dict[str, bool | None] = {
            "header_alg_rs256": False,
            "header_typ_at_jwt": False,
            "iss_matches": False,
            "aud_contains_expected": False,
            "claim_sub_present": False,
            "claim_exp_present": False,
            "claim_iat_present": False,
            "claim_jti_present": False,
            "claim_email_present": False,
            "claim_auth_provider_present": False,
            "sub_is_uuid": False,
            "exp_iat_are_numbers": False,
            "lifetime_within_limit": False,
            "signature_valid_current_key": False,
        }
        try:
            header = jwt.get_unverified_header(token)
            checks["header_alg_rs256"] = header.get("alg") == "RS256"
            checks["header_typ_at_jwt"] = header.get("typ") == "at+jwt"
            if not checks["header_alg_rs256"] or not checks["header_typ_at_jwt"]:
                logger.warning("jwt_verification checks=%s", checks)
                return None
            signed_claims = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                options={
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
            checks["signature_valid_current_key"] = True
            checks["iss_matches"] = signed_claims.get("iss") == self._issuer
            audience = signed_claims.get("aud")
            checks["aud_contains_expected"] = audience == self._audience
            for name in ("sub", "exp", "iat", "jti", "email", "auth_provider"):
                checks[f"claim_{name}_present"] = name in signed_claims
            subject = signed_claims.get("sub")
            try:
                if isinstance(subject, str):
                    UUID(subject)
                    checks["sub_is_uuid"] = True
            except ValueError:
                checks["sub_is_uuid"] = False
            exp, iat = signed_claims.get("exp"), signed_claims.get("iat")
            numeric = all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and isfinite(value)
                for value in (exp, iat)
            )
            checks["exp_iat_are_numbers"] = numeric
            checks["lifetime_within_limit"] = bool(
                numeric
                and exp is not None
                and iat is not None
                and exp > iat
                and exp - iat <= self._max_lifetime_seconds
            )
            if not all(
                value is True
                for name, value in checks.items()
                if name != "signature_valid_current_key"
            ):
                logger.warning("jwt_verification checks=%s", checks)
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
                        "jti",
                        "email",
                        "auth_provider",
                    ],
                },
            )
            if not all(
                isinstance(claims[name], (int, float))
                and not isinstance(claims[name], bool)
                and isfinite(claims[name])
                for name in ("iat", "exp")
            ):
                logger.warning("jwt_verification checks=%s", checks)
                return None
            if "nbf" in claims and (
                not isinstance(claims["nbf"], (int, float))
                or isinstance(claims["nbf"], bool)
                or not isfinite(claims["nbf"])
            ):
                logger.warning("jwt_verification checks=%s", checks)
                return None
            if (
                claims["exp"] <= claims["iat"]
                or claims["exp"] - claims["iat"] > self._max_lifetime_seconds
            ):
                logger.warning("jwt_verification checks=%s", checks)
                return None
            if not isinstance(claims["sub"], str):
                logger.warning("jwt_verification checks=%s", checks)
                return None
            user_id = UUID(claims["sub"])
            email = claims["email"]
            auth_provider = claims["auth_provider"]
            expires_at = datetime.fromtimestamp(claims["exp"], UTC)
            jti = claims["jti"]
        except (InvalidTokenError, KeyError, TypeError, ValueError, OverflowError):
            logger.warning("jwt_verification checks=%s", checks)
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
            logger.warning("jwt_verification checks=%s", checks)
            return None

        logger.info("jwt_verification checks=%s", checks)

        return IdentityTokenClaims(
            user_id=user_id,
            email=email,
            auth_provider=auth_provider,
            expires_at=expires_at,
        )
