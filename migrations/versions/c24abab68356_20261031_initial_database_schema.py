from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c24abab68356"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")
    op.execute("CREATE SCHEMA IF NOT EXISTS relations")
    op.execute("CREATE SCHEMA IF NOT EXISTS infrastructure")
    op.execute("CREATE SCHEMA IF NOT EXISTS projects")
    op.execute("CREATE SCHEMA IF NOT EXISTS automation")
    op.execute("CREATE SCHEMA IF NOT EXISTS development")
    op.execute("CREATE SCHEMA IF NOT EXISTS monitoring")
    op.execute("CREATE SCHEMA IF NOT EXISTS preferences")
    op.execute("CREATE SCHEMA IF NOT EXISTS synchronization")

    postgresql.ENUM(
        "project",
        "environment",
        "device",
        "connection",
        "service",
        "container",
        "database",
        "repository",
        "branch",
        "commit",
        "code_component",
        "dependency",
        "script",
        "script_execution",
        "relation",
        "event",
        "metric",
        "settings",
        "other",
        name="entity_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "belongs_to",
        "contains",
        "depends_on",
        "deploys_to",
        "runs_on",
        "connects_to",
        "exposes",
        "uses",
        "references",
        "communicates_with",
        "manages",
        "other",
        name="relation_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "automatic",
        "user_defined",
        "imported",
        name="relation_origin",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "macos",
        "windows",
        "linux",
        "ios",
        "android",
        "other",
        name="platform_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "active", "inactive", "revoked", name="client_device_status", create_type=False
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "physical",
        "virtual",
        "vps",
        "cloud",
        "other",
        name="device_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "software",
        "infrastructure",
        "fullstack",
        "other",
        name="project_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "active", "archived", name="project_status", create_type=False
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "local", "ssh", name="script_execution_type", create_type=False
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "safe",
        "moderate",
        "dangerous",
        "critical",
        name="script_risk_level",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("git", "other", name="repository_type", create_type=False).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "password",
        "ssh_key",
        "agent",
        "other",
        name="authentication_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "connected",
        "disconnected",
        "failed",
        "unknown",
        name="connection_status",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "project_created",
        "project_updated",
        "project_archived",
        "device_added",
        "device_updated",
        "device_removed",
        "connection_success",
        "connection_failure",
        "service_started",
        "service_stopped",
        "service_restarted",
        "container_started",
        "container_stopped",
        "container_restarted",
        "database_detected",
        "script_started",
        "script_completed",
        "script_failed",
        "git_operation",
        "repository_changed",
        "deployment",
        "infrastructure_check",
        "metric_collected",
        "relation_created",
        "relation_updated",
        "other",
        name="event_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "success",
        "failure",
        "warning",
        "informational",
        name="event_result",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "network_in",
        "network_out",
        "network_usage",
        "other",
        name="metric_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "percent",
        "bytes",
        "bytes_per_second",
        "megabytes",
        "gigabytes",
        "count",
        "other",
        name="metric_unit",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("global", "client", name="setting_scope", create_type=False).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "development",
        "testing",
        "staging",
        "production",
        "local",
        "other",
        name="environment_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "insert", "update", "delete", name="change_operation", create_type=False
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "synced",
        "pending",
        "syncing",
        "conflict",
        "failed",
        "offline",
        name="sync_status",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        "timeout",
        name="execution_status",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "file",
        "directory",
        "module",
        "package",
        "class",
        "function",
        "interface",
        "variable",
        "symbol",
        "other",
        name="component_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "systemd",
        "docker",
        "application",
        "database",
        "web_server",
        "other",
        name="service_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "running",
        "stopped",
        "restarting",
        "paused",
        "failed",
        "unknown",
        name="resource_status",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "import",
        "inheritance",
        "implementation",
        "composition",
        "aggregation",
        "reference",
        "call",
        "include",
        "other",
        name="dependency_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "created",
        "running",
        "paused",
        "restarting",
        "exited",
        "dead",
        "unknown",
        name="container_status",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "postgresql",
        "mysql",
        "mariadb",
        "mongodb",
        "redis",
        "sqlite",
        "other",
        name="dbms_type",
        create_type=False,
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("auth_provider", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="identity",
    )
    op.create_table(
        "relations",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column(
            "source_entity_type",
            postgresql.ENUM(
                "project",
                "environment",
                "device",
                "connection",
                "service",
                "container",
                "database",
                "repository",
                "branch",
                "commit",
                "code_component",
                "dependency",
                "script",
                "script_execution",
                "relation",
                "event",
                "metric",
                "settings",
                "other",
                name="entity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("source_entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "target_entity_type",
            postgresql.ENUM(
                "project",
                "environment",
                "device",
                "connection",
                "service",
                "container",
                "database",
                "repository",
                "branch",
                "commit",
                "code_component",
                "dependency",
                "script",
                "script_execution",
                "relation",
                "event",
                "metric",
                "settings",
                "other",
                name="entity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("target_entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "relation_type",
            postgresql.ENUM(
                "belongs_to",
                "contains",
                "depends_on",
                "deploys_to",
                "runs_on",
                "connects_to",
                "exposes",
                "uses",
                "references",
                "communicates_with",
                "manages",
                "other",
                name="relation_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "origin",
            postgresql.ENUM(
                "automatic",
                "user_defined",
                "imported",
                name="relation_origin",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="ck_relations_confidence",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="relations",
    )
    op.create_index(
        "ix_relations_project_id_source_entity_type_source_entity_id",
        "relations",
        ["project_id", "source_entity_type", "source_entity_id"],
        unique=False,
        schema="relations",
    )
    op.create_index(
        "ix_relations_project_id_target_entity_type_target_entity_id",
        "relations",
        ["project_id", "target_entity_type", "target_entity_id"],
        unique=False,
        schema="relations",
    )
    op.create_table(
        "client_devices",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "platform",
            postgresql.ENUM(
                "macos",
                "windows",
                "linux",
                "ios",
                "android",
                "other",
                name="platform_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("app_version", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "inactive",
                "revoked",
                name="client_device_status",
                create_type=False,
            ),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="identity",
    )
    op.create_table(
        "device_groups",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name"),
        schema="infrastructure",
    )
    op.create_table(
        "devices",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "device_type",
            postgresql.ENUM(
                "physical",
                "virtual",
                "vps",
                "cloud",
                "other",
                name="device_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("operating_system", sa.String(length=100), nullable=True),
        sa.Column("os_version", sa.String(length=100), nullable=True),
        sa.Column("architecture", sa.String(length=50), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="infrastructure",
    )
    op.create_table(
        "projects",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "project_type",
            postgresql.ENUM(
                "software",
                "infrastructure",
                "fullstack",
                "other",
                name="project_type",
                create_type=False,
            ),
            server_default=sa.text("'other'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "archived", name="project_status", create_type=False
            ),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projects",
    )
    op.create_table(
        "scripts",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("interpreter", sa.String(length=100), nullable=True),
        sa.Column(
            "execution_type",
            postgresql.ENUM(
                "local", "ssh", name="script_execution_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "risk_level",
            postgresql.ENUM(
                "safe",
                "moderate",
                "dangerous",
                "critical",
                name="script_risk_level",
                create_type=False,
            ),
            server_default=sa.text("'safe'"),
            nullable=False,
        ),
        sa.Column(
            "requires_confirmation",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="automation",
    )
    op.create_table(
        "repositories",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remote_url", sa.Text(), nullable=True),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column(
            "repository_type",
            postgresql.ENUM("git", "other", name="repository_type", create_type=False),
            server_default=sa.text("'git'"),
            nullable=False,
        ),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="development",
    )
    op.create_table(
        "sessions",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("client_device_id", sa.UUID(), nullable=True),
        sa.Column("token_hash", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_device_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        schema="identity",
    )
    op.create_table(
        "connections",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("host", sa.String(length=512), nullable=False),
        sa.Column("port", sa.Integer(), server_default=sa.text("22"), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column(
            "authentication_type",
            postgresql.ENUM(
                "password",
                "ssh_key",
                "agent",
                "other",
                name="authentication_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "connection_timeout",
            sa.Integer(),
            server_default=sa.text("30"),
            nullable=False,
        ),
        sa.Column(
            "is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_status",
            postgresql.ENUM(
                "connected",
                "disconnected",
                "failed",
                "unknown",
                name="connection_status",
                create_type=False,
            ),
            server_default=sa.text("'unknown'"),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("connection_timeout > 0", name="ck_connections_timeout"),
        sa.CheckConstraint("port BETWEEN 1 AND 65535", name="ck_connections_port"),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="infrastructure",
    )
    op.create_index(
        "uq_connections_one_default_per_device",
        "connections",
        ["device_id"],
        unique=True,
        schema="infrastructure",
        postgresql_where=sa.text("is_default = TRUE"),
    )
    op.create_table(
        "device_group_members",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"], ["infrastructure.devices.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["infrastructure.device_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "device_id"),
        schema="infrastructure",
    )
    op.create_table(
        "events",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                "project_created",
                "project_updated",
                "project_archived",
                "device_added",
                "device_updated",
                "device_removed",
                "connection_success",
                "connection_failure",
                "service_started",
                "service_stopped",
                "service_restarted",
                "container_started",
                "container_stopped",
                "container_restarted",
                "database_detected",
                "script_started",
                "script_completed",
                "script_failed",
                "git_operation",
                "repository_changed",
                "deployment",
                "infrastructure_check",
                "metric_collected",
                "relation_created",
                "relation_updated",
                "other",
                name="event_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            postgresql.ENUM(
                "project",
                "environment",
                "device",
                "connection",
                "service",
                "container",
                "database",
                "repository",
                "branch",
                "commit",
                "code_component",
                "dependency",
                "script",
                "script_execution",
                "relation",
                "event",
                "metric",
                "settings",
                "other",
                name="entity_type",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "result",
            postgresql.ENUM(
                "success",
                "failure",
                "warning",
                "informational",
                name="event_result",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("client_device_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_device_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="monitoring",
    )
    op.create_index(
        "ix_events_device_id_created_at",
        "events",
        ["device_id", "created_at"],
        unique=False,
        schema="monitoring",
    )
    op.create_index(
        "ix_events_event_type_created_at",
        "events",
        ["event_type", "created_at"],
        unique=False,
        schema="monitoring",
    )
    op.create_index(
        "ix_events_project_id_created_at",
        "events",
        ["project_id", "created_at"],
        unique=False,
        schema="monitoring",
    )
    op.create_table(
        "metrics",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column(
            "metric_type",
            postgresql.ENUM(
                "cpu_usage",
                "memory_usage",
                "disk_usage",
                "network_in",
                "network_out",
                "network_usage",
                "other",
                name="metric_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column(
            "unit",
            postgresql.ENUM(
                "percent",
                "bytes",
                "bytes_per_second",
                "megabytes",
                "gigabytes",
                "count",
                "other",
                name="metric_unit",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0", name="ck_metrics_nonnegative"),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="monitoring",
    )
    op.create_index(
        "ix_metrics_device_id_metric_type_collected_at",
        "metrics",
        ["device_id", "metric_type", "collected_at"],
        unique=False,
        schema="monitoring",
    )
    op.create_table(
        "settings",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("client_device_id", sa.UUID(), nullable=True),
        sa.Column(
            "scope",
            postgresql.ENUM(
                "global", "client", name="setting_scope", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_device_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="preferences",
    )
    op.create_index(
        "uq_settings_client",
        "settings",
        ["user_id", "client_device_id", "key"],
        unique=True,
        schema="preferences",
        postgresql_where=sa.text("scope = 'client' AND client_device_id IS NOT NULL"),
    )
    op.create_index(
        "uq_settings_global",
        "settings",
        ["user_id", "key"],
        unique=True,
        schema="preferences",
        postgresql_where=sa.text("scope = 'global'"),
    )
    op.create_table(
        "environments",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "environment_type",
            postgresql.ENUM(
                "development",
                "testing",
                "staging",
                "production",
                "local",
                "other",
                name="environment_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projects",
    )
    op.create_table(
        "project_devices",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projects",
    )
    op.create_index(
        "uq_project_devices_project_id_device_id",
        "project_devices",
        ["project_id", "device_id"],
        unique=True,
        schema="projects",
    )
    op.create_table(
        "change_log",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "entity_type",
            postgresql.ENUM(
                "project",
                "environment",
                "device",
                "connection",
                "service",
                "container",
                "database",
                "repository",
                "branch",
                "commit",
                "code_component",
                "dependency",
                "script",
                "script_execution",
                "relation",
                "event",
                "metric",
                "settings",
                "other",
                name="entity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "operation",
            postgresql.ENUM(
                "insert", "update", "delete", name="change_operation", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.Column(
            "sequence", sa.BigInteger(), sa.Identity(always=True), nullable=False
        ),
        sa.Column("changed_by_client_id", sa.UUID(), nullable=True),
        sa.Column("changed_by_user_id", sa.UUID(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_client_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["identity.users.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="synchronization",
    )
    op.create_index(
        "ix_change_log_user_id_created_at",
        "change_log",
        ["user_id", "created_at"],
        unique=False,
        schema="synchronization",
    )
    op.create_index(
        "ix_change_log_user_sequence",
        "change_log",
        ["user_id", "sequence"],
        unique=False,
        schema="synchronization",
    )
    op.create_index(
        "uq_change_log_entity_type_entity_id_version",
        "change_log",
        ["entity_type", "entity_id", "version"],
        unique=True,
        schema="synchronization",
    )
    op.create_index(
        "uq_change_log_sequence",
        "change_log",
        ["sequence"],
        unique=True,
        schema="synchronization",
    )
    op.create_table(
        "sync_state",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("client_device_id", sa.UUID(), nullable=False),
        sa.Column(
            "entity_type",
            postgresql.ENUM(
                "project",
                "environment",
                "device",
                "connection",
                "service",
                "container",
                "database",
                "repository",
                "branch",
                "commit",
                "code_component",
                "dependency",
                "script",
                "script_execution",
                "relation",
                "event",
                "metric",
                "settings",
                "other",
                name="entity_type",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("local_version", sa.BigInteger(), nullable=True),
        sa.Column("server_version", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "synced",
                "pending",
                "syncing",
                "conflict",
                "failed",
                "offline",
                name="sync_status",
                create_type=False,
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_device_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="synchronization",
    )
    op.create_index(
        "ix_sync_state_user_id_client_device_id",
        "sync_state",
        ["user_id", "client_device_id"],
        unique=False,
        schema="synchronization",
    )
    op.create_index(
        "uq_sync_state_device",
        "sync_state",
        ["user_id", "client_device_id"],
        unique=True,
        schema="synchronization",
        postgresql_where=sa.text("entity_type IS NULL AND entity_id IS NULL"),
    )
    op.create_index(
        "uq_sync_state_entity",
        "sync_state",
        ["client_device_id", "entity_type", "entity_id"],
        unique=True,
        schema="synchronization",
        postgresql_where=sa.text("entity_type IS NOT NULL AND entity_id IS NOT NULL"),
    )
    op.create_table(
        "script_executions",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("script_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("client_device_id", sa.UUID(), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "completed",
                "failed",
                "cancelled",
                "timeout",
                name="execution_status",
                create_type=False,
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sanitized_output_summary", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_device_id"],
            ["identity.client_devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["automation.scripts.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="automation",
    )
    op.create_index(
        "uq_script_executions_idempotency_key",
        "script_executions",
        ["idempotency_key"],
        unique=True,
        schema="automation",
    )
    op.create_table(
        "script_targets",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("script_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("environment_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["projects.environments.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["automation.scripts.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="automation",
    )
    op.create_index(
        "uq_script_targets_script_id_device_id_environment_id",
        "script_targets",
        ["script_id", "device_id", "environment_id"],
        unique=True,
        schema="automation",
    )
    op.create_table(
        "branches",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("commit_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "is_remote", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["development.repositories.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="development",
    )
    op.create_index(
        "uq_branches_repository_id_name_is_remote",
        "branches",
        ["repository_id", "name", "is_remote"],
        unique=True,
        schema="development",
    )
    op.create_table(
        "code_components",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column(
            "component_type",
            postgresql.ENUM(
                "file",
                "directory",
                "module",
                "package",
                "class",
                "function",
                "interface",
                "variable",
                "symbol",
                "other",
                name="component_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=100), nullable=True),
        sa.Column("symbol", sa.String(length=512), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("analysis_version", sa.String(length=100), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_commit_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["development.code_components.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["development.repositories.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="development",
    )
    op.create_index(
        "ix_code_components_repository_id_path_symbol",
        "code_components",
        ["repository_id", "path", "symbol"],
        unique=False,
        schema="development",
    )
    op.create_table(
        "commits",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("author_email", sa.String(length=320), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "changed_files", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("cached_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["development.repositories.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="development",
    )
    op.create_index(
        "uq_commits_repository_id_hash",
        "commits",
        ["repository_id", "hash"],
        unique=True,
        schema="development",
    )
    op.create_table(
        "services",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("environment_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "service_type",
            postgresql.ENUM(
                "systemd",
                "docker",
                "application",
                "database",
                "web_server",
                "other",
                name="service_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_identifier", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "running",
                "stopped",
                "restarting",
                "paused",
                "failed",
                "unknown",
                name="resource_status",
                create_type=False,
            ),
            server_default=sa.text("'unknown'"),
            nullable=False,
        ),
        sa.Column("last_status_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["projects.environments.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="infrastructure",
    )
    op.create_table(
        "dependencies",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("source_component_id", sa.UUID(), nullable=False),
        sa.Column("target_component_id", sa.UUID(), nullable=False),
        sa.Column(
            "dependency_type",
            postgresql.ENUM(
                "import",
                "inheritance",
                "implementation",
                "composition",
                "aggregation",
                "reference",
                "call",
                "include",
                "other",
                name="dependency_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_directed", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "source_type",
            postgresql.ENUM(
                "automatic",
                "user_defined",
                "imported",
                name="relation_origin",
                create_type=False,
            ),
            server_default=sa.text("'automatic'"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("analysis_version", sa.String(length=100), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="ck_dependencies_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["source_component_id"],
            ["development.code_components.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["target_component_id"],
            ["development.code_components.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="development",
    )
    op.create_index(
        "uq_dependencies_components_type",
        "dependencies",
        ["source_component_id", "target_component_id", "dependency_type"],
        unique=True,
        schema="development",
    )
    op.create_table(
        "containers",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("environment_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("container_runtime_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "created",
                "running",
                "paused",
                "restarting",
                "exited",
                "dead",
                "unknown",
                name="container_status",
                create_type=False,
            ),
            server_default=sa.text("'unknown'"),
            nullable=False,
        ),
        sa.Column("ports", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("volumes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("networks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["projects.environments.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["infrastructure.services.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="infrastructure",
    )
    op.create_index(
        "uq_containers_device_id_container_runtime_id",
        "containers",
        ["device_id", "container_runtime_id"],
        unique=True,
        schema="infrastructure",
    )
    op.create_table(
        "databases",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("environment_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("container_id", sa.UUID(), nullable=True),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "dbms_type",
            postgresql.ENUM(
                "postgresql",
                "mysql",
                "mariadb",
                "mongodb",
                "redis",
                "sqlite",
                "other",
                name="dbms_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("host", sa.String(length=512), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("database_name", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "running",
                "stopped",
                "restarting",
                "paused",
                "failed",
                "unknown",
                name="resource_status",
                create_type=False,
            ),
            server_default=sa.text("'unknown'"),
            nullable=False,
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "version", sa.BigInteger(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["container_id"],
            ["infrastructure.containers.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["projects.environments.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["infrastructure.services.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="infrastructure",
    )
    op.create_table(
        "logs_metadata",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("container_id", sa.UUID(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("records_count", sa.BigInteger(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["container_id"],
            ["infrastructure.containers.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["infrastructure.devices.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.projects.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["infrastructure.services.id"],
            initially="IMMEDIATE",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["identity.users.id"], initially="IMMEDIATE", deferrable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="monitoring",
    )


def downgrade() -> None:
    op.drop_table("logs_metadata", schema="monitoring")
    op.drop_table("databases", schema="infrastructure")
    op.drop_index(
        "uq_containers_device_id_container_runtime_id",
        table_name="containers",
        schema="infrastructure",
    )
    op.drop_table("containers", schema="infrastructure")
    op.drop_index(
        "uq_dependencies_components_type",
        table_name="dependencies",
        schema="development",
    )
    op.drop_table("dependencies", schema="development")
    op.drop_table("services", schema="infrastructure")
    op.drop_index(
        "uq_commits_repository_id_hash", table_name="commits", schema="development"
    )
    op.drop_table("commits", schema="development")
    op.drop_index(
        "ix_code_components_repository_id_path_symbol",
        table_name="code_components",
        schema="development",
    )
    op.drop_table("code_components", schema="development")
    op.drop_index(
        "uq_branches_repository_id_name_is_remote",
        table_name="branches",
        schema="development",
    )
    op.drop_table("branches", schema="development")
    op.drop_index(
        "uq_script_targets_script_id_device_id_environment_id",
        table_name="script_targets",
        schema="automation",
    )
    op.drop_table("script_targets", schema="automation")
    op.drop_index(
        "uq_script_executions_idempotency_key",
        table_name="script_executions",
        schema="automation",
    )
    op.drop_table("script_executions", schema="automation")
    op.drop_index(
        "uq_sync_state_entity",
        table_name="sync_state",
        schema="synchronization",
        postgresql_where=sa.text("entity_type IS NOT NULL AND entity_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_sync_state_device",
        table_name="sync_state",
        schema="synchronization",
        postgresql_where=sa.text("entity_type IS NULL AND entity_id IS NULL"),
    )
    op.drop_index(
        "ix_sync_state_user_id_client_device_id",
        table_name="sync_state",
        schema="synchronization",
    )
    op.drop_table("sync_state", schema="synchronization")
    op.drop_index(
        "uq_change_log_sequence", table_name="change_log", schema="synchronization"
    )
    op.drop_index(
        "uq_change_log_entity_type_entity_id_version",
        table_name="change_log",
        schema="synchronization",
    )
    op.drop_index(
        "ix_change_log_user_sequence", table_name="change_log", schema="synchronization"
    )
    op.drop_index(
        "ix_change_log_user_id_created_at",
        table_name="change_log",
        schema="synchronization",
    )
    op.drop_table("change_log", schema="synchronization")
    op.drop_index(
        "uq_project_devices_project_id_device_id",
        table_name="project_devices",
        schema="projects",
    )
    op.drop_table("project_devices", schema="projects")
    op.drop_table("environments", schema="projects")
    op.drop_index(
        "uq_settings_global",
        table_name="settings",
        schema="preferences",
        postgresql_where=sa.text("scope = 'global'"),
    )
    op.drop_index(
        "uq_settings_client",
        table_name="settings",
        schema="preferences",
        postgresql_where=sa.text("scope = 'client' AND client_device_id IS NOT NULL"),
    )
    op.drop_table("settings", schema="preferences")
    op.drop_index(
        "ix_metrics_device_id_metric_type_collected_at",
        table_name="metrics",
        schema="monitoring",
    )
    op.drop_table("metrics", schema="monitoring")
    op.drop_index(
        "ix_events_project_id_created_at", table_name="events", schema="monitoring"
    )
    op.drop_index(
        "ix_events_event_type_created_at", table_name="events", schema="monitoring"
    )
    op.drop_index(
        "ix_events_device_id_created_at", table_name="events", schema="monitoring"
    )
    op.drop_table("events", schema="monitoring")
    op.drop_table("device_group_members", schema="infrastructure")
    op.drop_index(
        "uq_connections_one_default_per_device",
        table_name="connections",
        schema="infrastructure",
        postgresql_where=sa.text("is_default = TRUE"),
    )
    op.drop_table("connections", schema="infrastructure")
    op.drop_table("sessions", schema="identity")
    op.drop_table("repositories", schema="development")
    op.drop_table("scripts", schema="automation")
    op.drop_table("projects", schema="projects")
    op.drop_table("devices", schema="infrastructure")
    op.drop_table("device_groups", schema="infrastructure")
    op.drop_table("client_devices", schema="identity")
    op.drop_index(
        "ix_relations_project_id_target_entity_type_target_entity_id",
        table_name="relations",
        schema="relations",
    )
    op.drop_index(
        "ix_relations_project_id_source_entity_type_source_entity_id",
        table_name="relations",
        schema="relations",
    )
    op.drop_table("relations", schema="relations")
    op.drop_table("users", schema="identity")
    postgresql.ENUM(name="dbms_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="container_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="dependency_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="resource_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="service_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="component_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="execution_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="sync_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="change_operation", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="environment_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="setting_scope", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="metric_unit", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="metric_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="event_result", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="event_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="connection_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="authentication_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="repository_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="script_risk_level", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="script_execution_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="project_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="project_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="device_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="client_device_status", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="platform_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="relation_origin", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="relation_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="entity_type", create_type=False).drop(
        op.get_bind(), checkfirst=True
    )
    op.execute("DROP SCHEMA IF EXISTS synchronization")
    op.execute("DROP SCHEMA IF EXISTS preferences")
    op.execute("DROP SCHEMA IF EXISTS monitoring")
    op.execute("DROP SCHEMA IF EXISTS development")
    op.execute("DROP SCHEMA IF EXISTS automation")
    op.execute("DROP SCHEMA IF EXISTS projects")
    op.execute("DROP SCHEMA IF EXISTS infrastructure")
    op.execute("DROP SCHEMA IF EXISTS relations")
    op.execute("DROP SCHEMA IF EXISTS identity")
