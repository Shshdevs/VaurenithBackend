from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "91e2a3b4c5d6"
down_revision: str | None = "78c4f3a6d219"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE entity_type ADD VALUE IF NOT EXISTS 'user'")
    op.execute("ALTER TYPE entity_type ADD VALUE IF NOT EXISTS 'project_device'")
    op.execute("ALTER TYPE entity_type ADD VALUE IF NOT EXISTS 'device_group'")
    op.execute("ALTER TYPE entity_type ADD VALUE IF NOT EXISTS 'sync_state'")
    op.add_column(
        "device_groups",
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        schema="infrastructure",
    )
    op.add_column(
        "project_devices",
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        schema="projects",
    )
    op.add_column(
        "sync_state",
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        schema="synchronization",
    )


def downgrade() -> None:
    op.drop_column("project_devices", "version", schema="projects")
    op.drop_column("sync_state", "version", schema="synchronization")
    op.drop_column("device_groups", "version", schema="infrastructure")
