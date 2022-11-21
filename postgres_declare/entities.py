from typing import Any, Sequence

from postgres_declare.base import Base


class Database(Base):
    # TODO add options for DB creation to __init__

    def create_statement(self) -> str:
        # TODO add options from init to customize this
        return f"CREATE DATABASE {self.name}"

    def exists_statement(self) -> str:
        return f"SELECT 1 AS result FROM pg_database WHERE datname={self.name}"


class Role(Base):
    def __init__(self, member_of: Sequence["Role"] | None = None, **kwargs: Any):
        # TODO add lots of options
        super().__init__(depends_on=member_of, **kwargs)

    def create_statement(self) -> str:
        return f"CREATE ROLE {self.name}"

    def exists_statement(self) -> str:
        return f"SELECT 1 AS result FROM pg_authid WHERE rolname={self.name}"
