from enum import Enum


class RelationOrigin(str, Enum):
    AUTOMATIC = "automatic"
    USER_DEFINED = "user_defined"
    IMPORTED = "imported"


class EntityType(str, Enum):
    USER = "user"
    PROJECT = "project"
    ENVIRONMENT = "environment"
    PROJECT_DEVICE = "project_device"
    DEVICE = "device"
    DEVICE_GROUP = "device_group"
    DEVICE_GROUP_MEMBER = "device_group_member"
    CONNECTION = "connection"
    SERVICE = "service"
    CONTAINER = "container"
    DATABASE = "database"
    REPOSITORY = "repository"
    BRANCH = "branch"
    COMMIT = "commit"
    CODE_COMPONENT = "code_component"
    DEPENDENCY = "dependency"
    SCRIPT = "script"
    SCRIPT_EXECUTION = "script_execution"
    SCRIPT_TARGET = "script_target"
    RELATION = "relation"
    EVENT = "event"
    LOG_METADATA = "log_metadata"
    CHANGE_LOG = "change_log"
    METRIC = "metric"
    SETTINGS = "settings"
    SYNC_STATE = "sync_state"
    OTHER = "other"


class RelationType(str, Enum):
    BELONGS_TO = "belongs_to"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    DEPLOYS_TO = "deploys_to"
    RUNS_ON = "runs_on"
    CONNECTS_TO = "connects_to"
    EXPOSES = "exposes"
    USES = "uses"
    REFERENCES = "references"
    COMMUNICATES_WITH = "communicates_with"
    MANAGES = "manages"
    OTHER = "other"
