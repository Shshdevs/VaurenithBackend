from app.domain.infrastructure import SystemIdentifier


def build_system_identifier(value: str | None) -> SystemIdentifier | None:
    if value is None or not value.strip():
        return None
    return SystemIdentifier(value)
