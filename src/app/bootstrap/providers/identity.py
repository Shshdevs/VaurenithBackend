from sqlalchemy.ext.asyncio import AsyncSession

from ...application.identity.use_cases import (
    AuthenticateIdentity,
    CreateUser,
    GetCurrentUser,
    VerifyIdentityToken,
)
from ...core.config import get_settings
from ...infrastructure.integrations.identity import JwtAccessTokenVerifier
from ...infrastructure.persistence.repositories.identity import (
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)


def provide_current_user(session: AsyncSession) -> GetCurrentUser:
    return GetCurrentUser(SqlAlchemyUserRepository(session))


def provide_create_user(session: AsyncSession) -> CreateUser:
    return CreateUser(SqlAlchemyUserRepository(session))


def provide_verify_identity_token() -> VerifyIdentityToken:
    secret = get_settings().auth_jwt_secret.get_secret_value()
    return VerifyIdentityToken(JwtAccessTokenVerifier(secret))


def provide_authenticate_identity(
    verify_identity_token: VerifyIdentityToken,
    session: AsyncSession,
) -> AuthenticateIdentity:
    return AuthenticateIdentity(
        verify_identity_token,
        SqlAlchemySessionRepository(session),
    )
