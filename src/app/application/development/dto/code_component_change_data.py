from app.domain.development.entities.code_component import CodeComponent


def code_component_change_data(component: CodeComponent) -> dict:
    return {
        "repository_id": str(component.repository_id),
        "parent_id": str(component.parent_id) if component.parent_id else None,
        "name": component.name,
        "path": component.path,
        "component_type": component.component_type.value,
        "language": component.language,
        "symbol": component.symbol,
        "start_line": component.start_line,
        "end_line": component.end_line,
        "analysis_version": component.analysis_version,
        "analyzed_at": component.analyzed_at.isoformat() if component.analyzed_at else None,
        "source_commit_hash": component.source_commit_hash,
    }
