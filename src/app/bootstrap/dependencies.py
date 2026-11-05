from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ..application.identity.dto.verified_identity import VerifiedIdentity
from ..application.identity.exceptions import InvalidIdentity
from ..application.identity.use_cases.authenticate_identity import (
    AuthenticateIdentity,
)
from ..application.identity.use_cases.create_user import CreateUser
from ..application.identity.use_cases.get_current_user import GetCurrentUser
from ..application.identity.use_cases.verify_identity_token import (
    VerifyIdentityToken,
)
from ..infrastructure.persistence.database import SessionLocal
from .providers import (
    provide_authenticate_identity,
    provide_create_user,
    provide_current_user,
    provide_database_health_check,
    provide_verify_identity_token,
)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_database_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def get_database_health_check(
    session: AsyncSession = Depends(get_database_session),
) -> CheckDatabaseHealth:
    return provide_database_health_check(session)


def get_current_user(
    session: AsyncSession = Depends(get_database_session),
) -> GetCurrentUser:
    return provide_current_user(session)


def get_create_user(
    session: AsyncSession = Depends(get_database_session),
) -> CreateUser:
    return provide_create_user(session)


def get_verify_identity_token() -> VerifyIdentityToken:
    return provide_verify_identity_token()


def get_authenticate_identity(
    session: AsyncSession = Depends(get_database_session),
    verify_identity_token: VerifyIdentityToken = Depends(get_verify_identity_token),
) -> AuthenticateIdentity:
    return provide_authenticate_identity(verify_identity_token, session)


def _get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None:
        raise InvalidIdentity("Bearer token is required")
    return credentials.credentials


async def get_authenticated_identity(
    token: str = Depends(_get_bearer_token),
    authenticate_identity: AuthenticateIdentity = Depends(get_authenticate_identity),
) -> VerifiedIdentity:
    return await authenticate_identity.execute(token)


def get_verified_identity(
    token: str = Depends(_get_bearer_token),
    verify_identity_token: VerifyIdentityToken = Depends(get_verify_identity_token),
) -> VerifiedIdentity:
    return verify_identity_token.execute(token)
