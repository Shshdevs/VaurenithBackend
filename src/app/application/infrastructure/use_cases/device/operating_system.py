from app.domain.infrastructure import OperatingSystem


def build_operating_system_info(
    name: str | None,
    version: str | None,
    architecture: str | None,
) -> OperatingSystem | None:
    values = (name, version, architecture)
    if not any(value is not None and value.strip() for value in values):
        return None
    return OperatingSystem(name=name, version=version, architecture=architecture)
