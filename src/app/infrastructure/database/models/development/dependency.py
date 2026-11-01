import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.development.code_component import (
        CodeComponent,
    )

from app.infrastructure.database.enums.common import RelationOrigin
from app.infrastructure.database.enums.development import DependencyType


class Dependency(Base):
    __tablename__ = "dependencies"
    __table_args__ = (
        Index(
            "uq_dependencies_components_type",
            "source_component_id",
            "target_component_id",
            "dependency_type",
            unique=True,
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="ck_dependencies_confidence",
        ),
        {"schema": "development"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    source_component_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "development.code_components.id", deferrable=True, initially="IMMEDIATE"
        ),
        nullable=False,
    )
    target_component_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "development.code_components.id", deferrable=True, initially="IMMEDIATE"
        ),
        nullable=False,
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(
            DependencyType,
            name="dependency_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    is_directed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    source_type: Mapped[RelationOrigin] = mapped_column(
        Enum(
            RelationOrigin,
            name="relation_origin",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'automatic'"),
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    analysis_version: Mapped[str | None] = mapped_column(String(100))
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Any | None] = mapped_column("metadata", JSONB)

    source_component: Mapped["CodeComponent"] = relationship(
        "CodeComponent",
        back_populates="dependencies_by_source_component",
        foreign_keys=[source_component_id],
    )

    target_component: Mapped["CodeComponent"] = relationship(
        "CodeComponent",
        back_populates="dependencies_by_target_component",
        foreign_keys=[target_component_id],
    )
