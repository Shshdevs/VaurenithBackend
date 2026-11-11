from collections.abc import Sequence

from alembic import op

revision: str = "d6e8f1a2b3c4"
down_revision: str | None = "b2d4e6f8a1c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE entity_type ADD VALUE IF NOT EXISTS 'device_group_member'")


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
                WHERE value = 'device_group_member'
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: device_group_member entity type is in use';
            END IF;
        END;
        $$;
        """
    )
