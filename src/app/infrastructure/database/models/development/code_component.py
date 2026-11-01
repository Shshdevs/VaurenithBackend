import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Index,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.development.dependency import Dependency
    from app.infrastructure.database.models.development.repository import Repository

from app.infrastructure.database.enums.development import ComponentType


class CodeComponent(Base):
    __tablename__ = "code_components"
    __table_args__ = (
        Index(
            "ix_code_components_repository_id_path_symbol",
            "repository_id",
            "path",
            "symbol",
        ),
        {"schema": "development"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "development.repositories.id", deferrable=True, initially="IMMEDIATE"
        ),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "development.code_components.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    component_type: Mapped[ComponentType] = mapped_column(
        Enum(
            ComponentType,
            name="component_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(String(100))
    symbol: Mapped[str | None] = mapped_column(String(512))
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    analysis_version: Mapped[str | None] = mapped_column(String(100))
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_commit_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="code_components", foreign_keys=[repository_id]
    )

    parent: Mapped["CodeComponent"] = relationship(
        "CodeComponent",
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side="CodeComponent.id",
    )

    children: Mapped[list["CodeComponent"]] = relationship(
        "CodeComponent", back_populates="parent", foreign_keys="CodeComponent.parent_id"
    )

    dependencies_by_source_component: Mapped[list["Dependency"]] = relationship(
        "Dependency",
        back_populates="source_component",
        foreign_keys="Dependency.source_component_id",
    )

    dependencies_by_target_component: Mapped[list["Dependency"]] = relationship(
        "Dependency",
        back_populates="target_component",
        foreign_keys="Dependency.target_component_id",
    )
