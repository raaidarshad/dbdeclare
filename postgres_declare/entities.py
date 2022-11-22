from typing import Any, Sequence

from sqlalchemy import TextClause, text

from postgres_declare.base import Base


class Database(Base):
    # TODO add options for DB creation to __init__

    def create_statement(self) -> TextClause:
        # TODO add options from init to customize this
        return text(f"CREATE DATABASE {self.name}")

    def exists_statement(self) -> TextClause:
        return text("SELECT 1 AS result FROM pg_database WHERE datname=:db").bindparams(
            db=self.name
        )


class Role(Base):
    def __init__(self, member_of: Sequence["Role"] | None = None, **kwargs: Any):
        # TODO add lots of options
        super().__init__(depends_on=member_of, **kwargs)

    def create_statement(self) -> TextClause:
        return text(f"CREATE ROLE {self.name}")

    def exists_statement(self) -> TextClause:
        return text("SELECT 1 AS result FROM pg_authid WHERE rolname=:role").bindparams(
            role=self.name
        )
