import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.automation.script_target import (
        ScriptTarget,
    )
    from app.infrastructure.persistence.models.infrastructure.container import Container
    from app.infrastructure.persistence.models.infrastructure.database import Database
    from app.infrastructure.persistence.models.infrastructure.service import Service
    from app.infrastructure.persistence.models.projects.project import Project

from app.domain.projects.enums import EnvironmentType


class Environment(Base):
    __tablename__ = "environments"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment_type: Mapped[EnvironmentType] = mapped_column(
        Enum(
            EnvironmentType,
            name="environment_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    configuration: Mapped[Any | None] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship(
        "Project", back_populates="environments", foreign_keys=[project_id]
    )

    services: Mapped[list["Service"]] = relationship(
        "Service", back_populates="environment", foreign_keys="Service.environment_id"
    )

    containers: Mapped[list["Container"]] = relationship(
        "Container",
        back_populates="environment",
        foreign_keys="Container.environment_id",
    )

    databases: Mapped[list["Database"]] = relationship(
        "Database", back_populates="environment", foreign_keys="Database.environment_id"
    )

    script_targets: Mapped[list["ScriptTarget"]] = relationship(
        "ScriptTarget",
        back_populates="environment",
        foreign_keys="ScriptTarget.environment_id",
    )
