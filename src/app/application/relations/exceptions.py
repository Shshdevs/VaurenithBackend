from app.application.common.exceptions import NotFound


class RelationNotFound(NotFound):
    def __init__(self, relation_id: str) -> None:
        super().__init__(f"Relation with id {relation_id} not found")


class RelationProjectNotFound(NotFound):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")


class RelationReferenceNotFound(NotFound):
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} entity with id {entity_id} not found in project")
