from uuid import UUID

from sqlalchemy import and_, delete, exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.relations.interfaces import RelationRepository
from app.domain.common.enums import EntityType
from app.domain.relations import Relation as RelationEntity
from app.infrastructure.persistence.models import (
    Branch,
    CodeComponent,
    Commit,
    Connection,
    Container,
    Database,
    Dependency,
    Device,
    DeviceGroup,
    DeviceGroupMember,
    Environment,
    Event,
    Metric,
    Project,
    ProjectDevice,
    Repository,
    Script,
    ScriptExecution,
    Service,
    Setting,
    SyncState,
    User,
)
from app.infrastructure.persistence.models import (
    Relation as RelationModel,
)


class SqlAlchemyRelationRepository(RelationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: UUID, project_id: UUID, relation_id: UUID
    ) -> RelationEntity | None:
        result = await self._session.execute(
            select(RelationModel).where(
                RelationModel.id == relation_id,
                RelationModel.project_id == project_id,
                self._owned_project(user_id, project_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def project_exists(self, user_id: UUID, project_id: UUID) -> bool:
        return bool(
            await self._session.scalar(select(self._owned_project(user_id, project_id)))
        )

    async def get_by_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
    ) -> list[RelationEntity]:
        statement = select(RelationModel).where(
            RelationModel.project_id == project_id,
            self._owned_project(user_id, project_id),
        )
        if entity_type is not None and entity_id is not None:
            statement = statement.where(
                or_(
                    and_(
                        RelationModel.source_entity_type == entity_type,
                        RelationModel.source_entity_id == entity_id,
                    ),
                    and_(
                        RelationModel.target_entity_type == entity_type,
                        RelationModel.target_entity_id == entity_id,
                    ),
                )
            )
        result = await self._session.execute(
            statement.order_by(RelationModel.created_at.desc(), RelationModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def reference_belongs_to_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> bool:
        statement = self._reference_statement(user_id, project_id, entity_type, entity_id)
        if statement is None:
            return entity_type is EntityType.OTHER and bool(
                await self._session.scalar(select(self._owned_project(user_id, project_id)))
            )
        result = await self._session.scalar(
            select(self._owned_project(user_id, project_id) & exists(statement))
        )
        return bool(result)

    async def create(self, user_id: UUID, relation: RelationEntity) -> None:
        if not await self._relation_references_are_valid(user_id, relation):
            raise ValueError("Relation references must belong to the project")
        self._session.add(self._to_model(relation))

    async def update(self, user_id: UUID, relation: RelationEntity) -> bool:
        if not await self._relation_references_are_valid(user_id, relation):
            raise ValueError("Relation references must belong to the project")
        result = await self._session.execute(
            update(RelationModel)
            .where(
                RelationModel.id == relation.id,
                RelationModel.project_id == relation.project_id,
                self._owned_project(user_id, relation.project_id),
            )
            .values(
                source_entity_type=relation.source_entity_type,
                source_entity_id=relation.source_entity_id,
                target_entity_type=relation.target_entity_type,
                target_entity_id=relation.target_entity_id,
                relation_type=relation.relation_type,
                confidence=relation.confidence,
                metadata_=relation.metadata,
                updated_at=relation.updated_at,
            )
            .returning(RelationModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UUID, project_id: UUID, relation_id: UUID) -> bool:
        result = await self._session.execute(
            delete(RelationModel)
            .where(
                RelationModel.id == relation_id,
                RelationModel.project_id == project_id,
                self._owned_project(user_id, project_id),
            )
            .returning(RelationModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def _relation_references_are_valid(
        self, user_id: UUID, relation: RelationEntity
    ) -> bool:
        return await self.reference_belongs_to_project(
            user_id,
            relation.project_id,
            relation.source_entity_type,
            relation.source_entity_id,
        ) and await self.reference_belongs_to_project(
            user_id,
            relation.project_id,
            relation.target_entity_type,
            relation.target_entity_id,
        )

    @staticmethod
    def _owned_project(user_id: UUID, project_id: UUID) -> Exists:
        return exists(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _reference_statement(
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ):
        device_in_project = SqlAlchemyRelationRepository._device_is_in_project(
            entity_id, user_id, project_id
        )
        match entity_type:
            case EntityType.USER:
                return select(User.id).where(User.id == entity_id, User.id == user_id)
            case EntityType.PROJECT:
                return select(Project.id).where(
                    Project.id == entity_id, Project.id == project_id
                )
            case EntityType.ENVIRONMENT:
                return select(Environment.id).where(
                    Environment.id == entity_id,
                    Environment.project_id == project_id,
                )
            case EntityType.PROJECT_DEVICE:
                return (
                    select(ProjectDevice.id)
                    .join(Device, Device.id == ProjectDevice.device_id)
                    .where(
                        ProjectDevice.id == entity_id,
                        ProjectDevice.project_id == project_id,
                        Device.user_id == user_id,
                    )
                )
            case EntityType.DEVICE:
                return select(Device.id).where(Device.id == entity_id, device_in_project)
            case EntityType.DEVICE_GROUP:
                return (
                    select(DeviceGroup.id)
                    .join(
                        DeviceGroupMember,
                        DeviceGroupMember.group_id == DeviceGroup.id,
                    )
                    .join(Device, Device.id == DeviceGroupMember.device_id)
                    .join(ProjectDevice, ProjectDevice.device_id == Device.id)
                    .where(
                        DeviceGroup.id == entity_id,
                        DeviceGroup.user_id == user_id,
                        Device.user_id == user_id,
                        ProjectDevice.project_id == project_id,
                    )
                )
            case EntityType.DEVICE_GROUP_MEMBER:
                return (
                    select(DeviceGroupMember.id)
                    .join(Device, Device.id == DeviceGroupMember.device_id)
                    .join(DeviceGroup, DeviceGroup.id == DeviceGroupMember.group_id)
                    .join(ProjectDevice, ProjectDevice.device_id == Device.id)
                    .where(
                        DeviceGroupMember.id == entity_id,
                        DeviceGroup.user_id == user_id,
                        Device.user_id == user_id,
                        ProjectDevice.project_id == project_id,
                    )
                )
            case EntityType.CONNECTION:
                return select(Connection.id).where(
                    Connection.id == entity_id,
                    SqlAlchemyRelationRepository._device_is_in_project(
                        Connection.device_id, user_id, project_id
                    ),
                )
            case EntityType.SERVICE:
                return select(Service.id).where(
                    Service.id == entity_id,
                    or_(
                        Service.project_id == project_id,
                        SqlAlchemyRelationRepository._device_is_in_project(
                            Service.device_id, user_id, project_id
                        ),
                    ),
                )
            case EntityType.CONTAINER:
                return select(Container.id).where(
                    Container.id == entity_id,
                    or_(
                        Container.project_id == project_id,
                        Container.environment_id.in_(
                            select(Environment.id).where(
                                Environment.project_id == project_id
                            )
                        ),
                        SqlAlchemyRelationRepository._device_is_in_project(
                            Container.device_id, user_id, project_id
                        ),
                    ),
                )
            case EntityType.DATABASE:
                return select(Database.id).where(
                    Database.id == entity_id,
                    or_(
                        Database.project_id == project_id,
                        Database.environment_id.in_(
                            select(Environment.id).where(
                                Environment.project_id == project_id
                            )
                        ),
                        SqlAlchemyRelationRepository._device_is_in_project(
                            Database.device_id, user_id, project_id
                        ),
                    ),
                )
            case EntityType.REPOSITORY:
                return select(Repository.id).where(
                    Repository.id == entity_id,
                    Repository.project_id == project_id,
                    Repository.deleted_at.is_(None),
                )
            case EntityType.BRANCH:
                return (
                    select(Branch.id)
                    .join(Repository, Repository.id == Branch.repository_id)
                    .where(
                        Branch.id == entity_id,
                        Repository.project_id == project_id,
                        Repository.deleted_at.is_(None),
                    )
                )
            case EntityType.COMMIT:
                return (
                    select(Commit.id)
                    .join(Repository, Repository.id == Commit.repository_id)
                    .where(
                        Commit.id == entity_id,
                        Repository.project_id == project_id,
                        Repository.deleted_at.is_(None),
                    )
                )
            case EntityType.CODE_COMPONENT:
                return (
                    select(CodeComponent.id)
                    .join(Repository, Repository.id == CodeComponent.repository_id)
                    .where(
                        CodeComponent.id == entity_id,
                        Repository.project_id == project_id,
                        Repository.deleted_at.is_(None),
                    )
                )
            case EntityType.DEPENDENCY:
                source = CodeComponent.__table__.alias("relation_source_component")
                target = CodeComponent.__table__.alias("relation_target_component")
                source_repository = Repository.__table__.alias("relation_source_repository")
                target_repository = Repository.__table__.alias("relation_target_repository")
                return (
                    select(Dependency.id)
                    .join(
                        source,
                        source.c.id == Dependency.source_component_id,
                    )
                    .join(
                        source_repository,
                        source_repository.c.id == source.c.repository_id,
                    )
                    .join(
                        target,
                        target.c.id == Dependency.target_component_id,
                    )
                    .join(
                        target_repository,
                        target_repository.c.id == target.c.repository_id,
                    )
                    .where(
                        Dependency.id == entity_id,
                        or_(
                            source_repository.c.project_id == project_id,
                            target_repository.c.project_id == project_id,
                        ),
                    )
                )
            case EntityType.SCRIPT:
                return select(Script.id).where(
                    Script.id == entity_id,
                    or_(Script.project_id == project_id, Script.user_id == user_id),
                    Script.deleted_at.is_(None),
                )
            case EntityType.SCRIPT_EXECUTION:
                return (
                    select(ScriptExecution.id)
                    .join(Script, Script.id == ScriptExecution.script_id)
                    .where(
                        ScriptExecution.id == entity_id,
                        or_(
                            Script.project_id == project_id,
                            Script.user_id == user_id,
                        ),
                        Script.deleted_at.is_(None),
                    )
                )
            case EntityType.RELATION:
                return select(RelationModel.id).where(
                    RelationModel.id == entity_id,
                    RelationModel.project_id == project_id,
                )
            case EntityType.EVENT:
                return select(Event.id).where(
                    Event.id == entity_id,
                    Event.user_id == user_id,
                    Event.project_id == project_id,
                )
            case EntityType.METRIC:
                return select(Metric.id).where(
                    Metric.id == entity_id,
                    SqlAlchemyRelationRepository._device_is_in_project(
                        Metric.device_id, user_id, project_id
                    ),
                )
            case EntityType.SETTINGS:
                return select(Setting.id).where(
                    Setting.id == entity_id, Setting.user_id == user_id
                )
            case EntityType.SYNC_STATE:
                return select(SyncState.id).where(
                    SyncState.id == entity_id, SyncState.user_id == user_id
                )
            case _:
                return None

    @staticmethod
    def _device_is_in_project(device_id, user_id: UUID, project_id: UUID) -> Exists:
        return exists(
            select(ProjectDevice.id)
            .join(Device, Device.id == ProjectDevice.device_id)
            .where(
                ProjectDevice.project_id == project_id,
                ProjectDevice.device_id == device_id,
                Device.user_id == user_id,
            )
        )

    @staticmethod
    def _to_entity(model: RelationModel) -> RelationEntity:
        return RelationEntity(
            entity_id=model.id,
            project_id=model.project_id,
            source_entity_type=model.source_entity_type,
            source_entity_id=model.source_entity_id,
            target_entity_type=model.target_entity_type,
            target_entity_id=model.target_entity_id,
            relation_type=model.relation_type,
            origin=model.origin,
            confidence=model.confidence,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: RelationEntity) -> RelationModel:
        return RelationModel(
            id=entity.id,
            project_id=entity.project_id,
            source_entity_type=entity.source_entity_type,
            source_entity_id=entity.source_entity_id,
            target_entity_type=entity.target_entity_type,
            target_entity_id=entity.target_entity_id,
            relation_type=entity.relation_type,
            origin=entity.origin,
            confidence=entity.confidence,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
