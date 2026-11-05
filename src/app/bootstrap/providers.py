from sqlalchemy.ext.asyncio import AsyncSession

from ..application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ..application.identity.use_cases.authenticate_identity import (
    AuthenticateIdentity,
)
from ..application.identity.use_cases.create_user import CreateUser
from ..application.identity.use_cases.get_current_user import GetCurrentUser
from ..application.identity.use_cases.verify_identity_token import (
    VerifyIdentityToken,
)
from ..core.config import get_settings
from ..infrastructure.integrations.database.health_checker import (
    SqlAlchemyHealthChecker,
)
from ..infrastructure.integrations.identity.jwt_access_token_verifier import (
    JwtAccessTokenVerifier,
)
from ..infrastructure.persistence.repositories.identity import (
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)


def provide_database_health_check(session: AsyncSession) -> CheckDatabaseHealth:
    return CheckDatabaseHealth(SqlAlchemyHealthChecker(session))


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
