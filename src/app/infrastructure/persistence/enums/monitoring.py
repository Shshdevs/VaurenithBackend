from enum import Enum


class EventResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    INFORMATIONAL = "informational"


class EventType(str, Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_ARCHIVED = "project_archived"
    DEVICE_ADDED = "device_added"
    DEVICE_UPDATED = "device_updated"
    DEVICE_REMOVED = "device_removed"
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_FAILURE = "connection_failure"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_RESTARTED = "service_restarted"
    CONTAINER_STARTED = "container_started"
    CONTAINER_STOPPED = "container_stopped"
    CONTAINER_RESTARTED = "container_restarted"
    DATABASE_DETECTED = "database_detected"
    SCRIPT_STARTED = "script_started"
    SCRIPT_COMPLETED = "script_completed"
    SCRIPT_FAILED = "script_failed"
    GIT_OPERATION = "git_operation"
    REPOSITORY_CHANGED = "repository_changed"
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE_CHECK = "infrastructure_check"
    METRIC_COLLECTED = "metric_collected"
    RELATION_CREATED = "relation_created"
    RELATION_UPDATED = "relation_updated"
    OTHER = "other"


class MetricType(str, Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IN = "network_in"
    NETWORK_OUT = "network_out"
    NETWORK_USAGE = "network_usage"
    OTHER = "other"


class MetricUnit(str, Enum):
    PERCENT = "percent"
    BYTES = "bytes"
    BYTES_PER_SECOND = "bytes_per_second"
    MEGABYTES = "megabytes"
    GIGABYTES = "gigabytes"
    COUNT = "count"
    OTHER = "other"
