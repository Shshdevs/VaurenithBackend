from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.use_cases import (
    AuthenticateIdentity,
    CreateDeviceSession,
    CreateUser,
    DeleteUser,
    GetClientDevice,
    GetCurrentUser,
    ListClientDevices,
    ListDeviceSessions,
    RegisterClientDevice,
    RevokeClientDevice,
    RevokeSession,
    SetClientDeviceStatus,
    UpdateClientDevice,
    VerifyIdentityToken,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.core.config import get_settings
from app.infrastructure.integrations.identity import JwtAccessTokenVerifier
from app.infrastructure.persistence.repositories.identity import (
    SqlAlchemyClientDeviceRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_current_user(session: AsyncSession) -> GetCurrentUser:
    return GetCurrentUser(SqlAlchemyUserRepository(session))


def provide_create_user(session: AsyncSession) -> CreateUser:
    return CreateUser(
        SqlAlchemyUserRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_user(session: AsyncSession) -> DeleteUser:
    return DeleteUser(SqlAlchemyUserRepository(session), SqlAlchemyUnitOfWork(session))


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


def provide_revoke_session(session: AsyncSession) -> RevokeSession:
    return RevokeSession(
        SqlAlchemySessionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_register_client_device(session: AsyncSession) -> RegisterClientDevice:
    return RegisterClientDevice(
        SqlAlchemyUserRepository(session),
        SqlAlchemyClientDeviceRepository(session),
        SqlAlchemySessionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_list_client_devices(session: AsyncSession) -> ListClientDevices:
    return ListClientDevices(SqlAlchemyClientDeviceRepository(session))


def provide_get_client_device(session: AsyncSession) -> GetClientDevice:
    return GetClientDevice(SqlAlchemyClientDeviceRepository(session))


def provide_update_client_device(session: AsyncSession) -> UpdateClientDevice:
    return UpdateClientDevice(
        SqlAlchemyClientDeviceRepository(session), SqlAlchemyUnitOfWork(session)
    )


def provide_create_device_session(session: AsyncSession) -> CreateDeviceSession:
    return CreateDeviceSession(
        SqlAlchemyClientDeviceRepository(session),
        SqlAlchemySessionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_list_device_sessions(session: AsyncSession) -> ListDeviceSessions:
    return ListDeviceSessions(
        SqlAlchemyClientDeviceRepository(session),
        SqlAlchemySessionRepository(session),
    )


def provide_set_client_device_status(session: AsyncSession) -> SetClientDeviceStatus:
    return SetClientDeviceStatus(
        SqlAlchemyClientDeviceRepository(session),
        SqlAlchemySessionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_revoke_client_device(session: AsyncSession) -> RevokeClientDevice:
    return RevokeClientDevice(
        SqlAlchemyClientDeviceRepository(session),
        SqlAlchemySessionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )
