from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity import UserAlreadyExists, UserRepository
from app.domain.identity import ClientDevice as ClientDeviceEntity
from app.domain.identity import EmailAddress
from app.domain.identity import Session as SessionEntity
from app.domain.identity import User as UserEntity
from app.infrastructure.persistence.models.automation import (
    Script,
    ScriptExecution,
    ScriptTarget,
)
from app.infrastructure.persistence.models.development import (
    Branch,
    CodeComponent,
    Commit,
    Dependency,
    Repository,
)
from app.infrastructure.persistence.models.identity import ClientDevice, Session, User
from app.infrastructure.persistence.models.infrastructure import (
    Connection,
    Container,
    Database,
    Device,
    DeviceGroup,
    DeviceGroupMember,
    Service,
)
from app.infrastructure.persistence.models.monitoring import Event, LogsMetadata, Metric
from app.infrastructure.persistence.models.preferences import Setting
from app.infrastructure.persistence.models.projects import (
    Environment,
    Project,
    ProjectDevice,
)
from app.infrastructure.persistence.models.relations import Relation
from app.infrastructure.persistence.models.synchronization import ChangeLog, SyncState


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def register(
        self,
        user: UserEntity,
        client_device: ClientDeviceEntity,
        session: SessionEntity,
    ) -> None:
        user_model = User(
            id=user.id,
            email=user.email.value,
            display_name=user.display_name,
            nickname=user.nickname,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        session_model = Session(
            id=session.id,
            user_id=session.user_id,
            client_device_id=session.client_device_id,
            token_hash=session.token_hash.value,
            expires_at=session.expires_at,
            created_at=session.created_at,
            revoked_at=session.revoked_at,
        )
        client_device_model = ClientDevice(
            id=client_device.id,
            user_id=client_device.user_id,
            name=client_device.name,
            slug=client_device.slug,
            platform=client_device.platform,
            app_version=client_device.app_version,
            status=client_device.status,
            registered_at=client_device.registered_at,
            last_seen_at=client_device.last_seen_at,
            revoked_at=client_device.revoked_at,
        )
        client_device_model.user = user_model
        session_model.user = user_model
        session_model.client_device = client_device_model
        self._session.add_all([user_model, client_device_model, session_model])
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise UserAlreadyExists(str(user.email)) from error

    async def delete(self, user_id: UUID) -> bool:
        user_result = await self._session.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        )
        if user_result.scalar_one_or_none() is None:
            return False

        project_ids = select(Project.id).where(Project.user_id == user_id)
        environment_ids = select(Environment.id).where(
            Environment.project_id.in_(project_ids)
        )
        device_ids = select(Device.id).where(Device.user_id == user_id)
        client_device_ids = select(ClientDevice.id).where(ClientDevice.user_id == user_id)
        group_ids = select(DeviceGroup.id).where(DeviceGroup.user_id == user_id)
        service_ids = select(Service.id).where(
            Service.device_id.in_(device_ids)
            | Service.project_id.in_(project_ids)
            | Service.environment_id.in_(environment_ids)
        )
        container_ids = select(Container.id).where(
            Container.device_id.in_(device_ids)
            | Container.project_id.in_(project_ids)
            | Container.environment_id.in_(environment_ids)
            | Container.service_id.in_(service_ids)
        )
        repository_ids = select(Repository.id).where(Repository.project_id.in_(project_ids))
        script_ids = select(Script.id).where(Script.project_id.in_(project_ids))
        component_ids = select(CodeComponent.id).where(
            CodeComponent.repository_id.in_(repository_ids)
        )

        await self._session.execute(
            delete(ChangeLog).where(
                (ChangeLog.user_id == user_id) | (ChangeLog.changed_by_user_id == user_id)
            )
        )
        await self._session.execute(delete(SyncState).where(SyncState.user_id == user_id))
        await self._session.execute(
            delete(Setting).where(
                (Setting.user_id == user_id)
                | Setting.client_device_id.in_(client_device_ids)
            )
        )
        await self._session.execute(
            delete(ScriptExecution).where(
                ScriptExecution.script_id.in_(script_ids)
                | ScriptExecution.device_id.in_(device_ids)
                | ScriptExecution.client_device_id.in_(client_device_ids)
            )
        )
        await self._session.execute(
            delete(ScriptTarget).where(
                ScriptTarget.script_id.in_(script_ids)
                | ScriptTarget.device_id.in_(device_ids)
                | ScriptTarget.environment_id.in_(environment_ids)
            )
        )
        await self._session.execute(delete(Script).where(Script.id.in_(script_ids)))
        await self._session.execute(
            delete(Dependency).where(
                Dependency.source_component_id.in_(component_ids)
                | Dependency.target_component_id.in_(component_ids)
            )
        )
        await self._session.execute(
            delete(CodeComponent).where(CodeComponent.repository_id.in_(repository_ids))
        )
        await self._session.execute(
            delete(Commit).where(Commit.repository_id.in_(repository_ids))
        )
        await self._session.execute(
            delete(Branch).where(Branch.repository_id.in_(repository_ids))
        )
        await self._session.execute(
            delete(Repository).where(Repository.id.in_(repository_ids))
        )
        await self._session.execute(
            delete(Relation).where(Relation.project_id.in_(project_ids))
        )
        await self._session.execute(
            delete(Event).where(
                (Event.user_id == user_id)
                | Event.project_id.in_(project_ids)
                | Event.device_id.in_(device_ids)
                | Event.client_device_id.in_(client_device_ids)
            )
        )
        await self._session.execute(
            delete(LogsMetadata).where(
                (LogsMetadata.user_id == user_id)
                | LogsMetadata.project_id.in_(project_ids)
                | LogsMetadata.device_id.in_(device_ids)
                | LogsMetadata.service_id.in_(service_ids)
                | LogsMetadata.container_id.in_(container_ids)
            )
        )
        await self._session.execute(delete(Metric).where(Metric.device_id.in_(device_ids)))
        await self._session.execute(
            delete(DeviceGroupMember).where(
                DeviceGroupMember.group_id.in_(group_ids)
                | DeviceGroupMember.device_id.in_(device_ids)
            )
        )
        await self._session.execute(
            delete(Database).where(
                Database.device_id.in_(device_ids)
                | Database.project_id.in_(project_ids)
                | Database.environment_id.in_(environment_ids)
                | Database.container_id.in_(container_ids)
                | Database.service_id.in_(service_ids)
            )
        )
        await self._session.execute(
            delete(Container).where(Container.id.in_(container_ids))
        )
        await self._session.execute(delete(Service).where(Service.id.in_(service_ids)))
        await self._session.execute(
            delete(Database).where(
                Database.container_id.in_(container_ids)
                | Database.service_id.in_(service_ids)
            )
        )
        await self._session.execute(
            delete(Connection).where(Connection.device_id.in_(device_ids))
        )
        await self._session.execute(
            delete(ProjectDevice).where(
                ProjectDevice.project_id.in_(project_ids)
                | ProjectDevice.device_id.in_(device_ids)
            )
        )
        await self._session.execute(
            delete(Environment).where(Environment.project_id.in_(project_ids))
        )
        await self._session.execute(delete(Project).where(Project.id.in_(project_ids)))
        await self._session.execute(
            delete(DeviceGroup).where(DeviceGroup.id.in_(group_ids))
        )
        await self._session.execute(delete(Device).where(Device.id.in_(device_ids)))
        await self._session.execute(
            delete(Session).where(
                (Session.user_id == user_id)
                | Session.client_device_id.in_(client_device_ids)
            )
        )
        await self._session.execute(
            delete(ClientDevice).where(ClientDevice.user_id == user_id)
        )
        await self._session.execute(delete(User).where(User.id == user_id))
        return True

    @staticmethod
    def _to_entity(model: User) -> UserEntity:
        return UserEntity(
            entity_id=model.id,
            email=EmailAddress(model.email),
            display_name=model.display_name,
            auth_provider=model.auth_provider,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
