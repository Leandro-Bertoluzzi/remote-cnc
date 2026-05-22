class EntityNotFoundError(Exception):
    pass


class DatabaseError(Exception):
    pass


class Unauthorized(Exception):
    pass


class DuplicatedFileError(Exception):
    pass


class DuplicatedFileNameError(Exception):
    pass


class InvalidTaskStatus(Exception):
    pass


class InvalidRole(Exception):
    pass


class DuplicatedUserError(Exception):
    pass
