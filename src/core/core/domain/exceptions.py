class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class AuthorizationError(DomainError):
    pass


class EntityNotFoundError(NotFoundError):
    pass


class Unauthorized(AuthorizationError):
    pass


class PersistenceError(DomainError):
    pass


class DuplicatedFileError(ConflictError):
    pass


class DuplicatedFileNameError(ConflictError):
    pass


class InvalidTaskStatus(ValidationError):
    pass


class InvalidRole(ValidationError):
    pass


class DuplicatedUserError(ConflictError):
    pass


class InvalidFile(ValidationError):
    pass


class FileSystemError(DomainError):
    pass
