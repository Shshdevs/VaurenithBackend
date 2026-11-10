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
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM (
                    SELECT entity_type::text AS value
                    FROM synchronization.change_log
                    UNION ALL
                    SELECT entity_type::text
                    FROM synchronization.sync_state
                    WHERE entity_type IS NOT NULL
                    UNION ALL
                    SELECT source_entity_type::text
                    FROM relations.relations
                    UNION ALL
                    SELECT target_entity_type::text
                    FROM relations.relations
                    UNION ALL
                    SELECT entity_type::text
                    FROM monitoring.events
                    WHERE entity_type IS NOT NULL
                ) AS used_entity_types
                WHERE value IN ('user', 'project_device', 'device_group', 'sync_state')
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: new entity_type labels are in use';
            END IF;
        END;
        $$;
        """
    )
    op.drop_column("project_devices", "version", schema="projects")
    op.drop_column("sync_state", "version", schema="synchronization")
    op.drop_column("device_groups", "version", schema="infrastructure")
