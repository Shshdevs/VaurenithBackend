from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.identity import InvalidIdentity
from ...application.identity.dto import VerifiedIdentity
from ...application.identity.use_cases import (
    AuthenticateIdentity,
    CreateUser,
    GetCurrentUser,
    VerifyIdentityToken,
)
from ..providers import (
    provide_authenticate_identity,
    provide_create_user,
    provide_current_user,
    provide_verify_identity_token,
)
from .database import get_database_session

_bearer_scheme = HTTPBearer(auto_error=False)


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
