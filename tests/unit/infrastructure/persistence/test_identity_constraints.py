from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.identity.session import Session


def test_session_requires_device_and_enforces_composite_owner_foreign_key() -> None:
    assert Session.__table__.c.client_device_id.nullable is False
    owner_device_fk = next(
        constraint
        for constraint in Session.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        and constraint.name == "fk_sessions_user_client_device"
    )
    assert [column.name for column in owner_device_fk.columns] == [
        "user_id",
        "client_device_id",
    ]
    assert [element.target_fullname for element in owner_device_fk.elements] == [
        "identity.client_devices.user_id",
        "identity.client_devices.id",
    ]


def test_identity_tables_declare_unique_and_lifecycle_constraints() -> None:
    device_constraints = ClientDevice.__table__.constraints
    session_constraints = Session.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_client_devices_user_id_id"
        for constraint in device_constraints
    )
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_client_devices_revoked_at_status"
        for constraint in device_constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_sessions_token_hash"
        for constraint in session_constraints
    )
