from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from sqlalchemy import TextClause, text

from postgres_declare.entities.role import Role


class Privilege(StrEnum):
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
    TEMP = "TEMP"
    EXECUTE = "EXECUTE"
    ALTER_SYSTEM = "ALTER SYSTEM"


@dataclass
class Grant:
    privileges: Sequence[Privilege]
    grantees: Sequence[Role]


class Grantable:
    def __init__(self, name: str):
        self.name = name
        self.grants: list[Grant] = []

    def grant(self, grants: Sequence[Grant]) -> None:
        self.grants.extend(grants)

    @abstractmethod
    def _grant(self) -> None:
        pass

    def _grant_statements(self) -> Sequence[TextClause]:
        # TODO check privileges for the type, or just let postgres handle the error?
        return [
            text(
                f"GRANT {self._format_privileges(grant)} ON {self.__class__.__name__.upper()} {self.name} TO {self._format_grantees(grant)}"
            )
            for grant in self.grants
        ]

    @staticmethod
    def _format_privileges(grant: Grant) -> str:
        return ", ".join([p for p in grant.privileges])

    @staticmethod
    def _format_grantees(grant: Grant) -> str:
        return ", ".join([r.name for r in grant.grantees])
