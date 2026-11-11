from sqlalchemy.ext.asyncio import AsyncSession

from app.application.preferences.use_cases.settings import (
    CreateSetting,
    DeleteSetting,
    GetSetting,
    GetSettings,
    UpdateSetting,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.preferences import (
    SqlAlchemySettingRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _repository(session: AsyncSession) -> SqlAlchemySettingRepository:
    return SqlAlchemySettingRepository(session)


def provide_get_settings(session: AsyncSession) -> GetSettings:
    return GetSettings(_repository(session))


def provide_get_setting(session: AsyncSession) -> GetSetting:
    return GetSetting(_repository(session))


def provide_create_setting(session: AsyncSession) -> CreateSetting:
    return CreateSetting(
        _repository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_update_setting(session: AsyncSession) -> UpdateSetting:
    return UpdateSetting(
        _repository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_setting(session: AsyncSession) -> DeleteSetting:
    return DeleteSetting(
        _repository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
