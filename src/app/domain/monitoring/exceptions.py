from ..common.exceptions import DomainError


class InvalidEvent(DomainError):
    pass


class InvalidLogMetadata(DomainError):
    pass


class InvalidMetric(DomainError):
    pass
