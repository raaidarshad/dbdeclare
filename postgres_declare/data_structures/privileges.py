from enum import StrEnum


class Privilege(StrEnum):
    """
    Enumeration of all possible privileges, see official documentation `here <https://www.postgresql.org/docs/current/ddl-priv.html#PRIVILEGE-ABBREVS-TABLE>`_.
    """

    ALL_PRIVILEGES = "ALL PRIVILEGES"
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    REFERENCES = "REFERENCES"
    TRIGGER = "TRIGGER"
    USAGE = "USAGE"
    CREATE = "CREATE"
    CONNECT = "CONNECT"
    TEMPORARY = "TEMPORARY"
    EXECUTE = "EXECUTE"
    ALTER_SYSTEM = "ALTER SYSTEM"
