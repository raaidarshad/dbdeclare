class PostgresDeclareError(Exception):
    pass


class NoEngineError(PostgresDeclareError):
    pass


class EntityExistsError(PostgresDeclareError):
    pass


class InvalidPrivilegeError(PostgresDeclareError):
    pass
