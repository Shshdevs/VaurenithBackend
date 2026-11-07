import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
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
from app.infrastructure.persistence.slug_defaults import slug_from_name

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.automation.script_execution import (
        ScriptExecution,
    )
    from app.infrastructure.persistence.models.automation.script_target import (
        ScriptTarget,
    )
    from app.infrastructure.persistence.models.projects.project import Project

from app.domain.automation.enums import (
    ScriptExecutionType,
    ScriptRiskLevel,
)


class Script(Base):
    __tablename__ = "scripts"
    __table_args__ = {"schema": "automation"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, default=slug_from_name
    )
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    interpreter: Mapped[str | None] = mapped_column(String(100))
    execution_type: Mapped[ScriptExecutionType] = mapped_column(
        Enum(
            ScriptExecutionType,
            name="script_execution_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    parameters: Mapped[Any | None] = mapped_column(JSONB)
    risk_level: Mapped[ScriptRiskLevel] = mapped_column(
        Enum(
            ScriptRiskLevel,
            name="script_risk_level",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'safe'"),
    )
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
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
        "Project", back_populates="scripts", foreign_keys=[project_id]
    )

    script_targets: Mapped[list["ScriptTarget"]] = relationship(
        "ScriptTarget", back_populates="script", foreign_keys="ScriptTarget.script_id"
    )

    script_executions: Mapped[list["ScriptExecution"]] = relationship(
        "ScriptExecution",
        back_populates="script",
        foreign_keys="ScriptExecution.script_id",
    )
