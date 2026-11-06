from app.domain.common.exceptions import DomainError


class InvalidEmail(DomainError):
    pass


class InvalidTokenHash(DomainError):
    pass


class InvalidSession(DomainError):
    pass


class InvalidClientDevice(DomainError):
    pass
