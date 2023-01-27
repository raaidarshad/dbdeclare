from __future__ import annotations

from typing import Sequence, Type

from sqlalchemy import Inspector, inspect
from sqlalchemy.orm import DeclarativeBase

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.database import Database
from postgres_declare.entities.database_entity import DatabaseEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema
from postgres_declare.mixins.grantable import Grantable
from postgres_declare.mixins.sql import SQLBase


class DatabaseContent(DatabaseEntity):
    def __init__(
        self,
        name: str,
        sqlalchemy_base: Type[DeclarativeBase],
        database: Database,
        schemas: Sequence[Schema] | None = None,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        super().__init__(name=name, depends_on=depends_on, database=database, check_if_exists=check_if_exists)
        self.base = sqlalchemy_base
        # schemas doesn't do anything since __table_args__ in sqlalchemy defines the schema
        # BUT it helps to have it as a dependency here to remind the user to make schemas they intend to use
        self.schemas = schemas
        self.tables: dict[str, Table] = {
            table.name: Table(name=table.name, database_content=self, schema=table.schema)
            for table in self.base.metadata.tables.values()
        }

    def _create(self) -> None:
        self.base.metadata.create_all(self.database.db_engine())

    def _exists(self) -> bool:
        inspector: Inspector = inspect(self.database.db_engine())
        return all(
            [
                inspector.has_table(table_name=table.name, schema=table.schema)
                for table in self.base.metadata.tables.values()
            ]
        )

    def _drop(self) -> None:
        self.base.metadata.drop_all(self.database.db_engine())


class Table(SQLBase, Grantable):
    def __init__(self, name: str, database_content: DatabaseContent, schema: str | None = "public"):
        super().__init__(name=name)
        self.database_content = database_content
        self.schema = schema

    def __hash__(self) -> int:
        return hash((self.name, self.__class__.__name__, self.database_content.name, self.schema))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.name, self.__class__.__name__, self.database_content.name, self.schema) == (
            other.name,
            other.__class__.__name__,
            other.database_content.name,
            self.schema,
        )

    def grant(self, grants: Sequence[GrantTo]) -> None:
        super().grant(grants=grants)
        self._fix_entity_order(grants=grants, target_entity=self.database_content)

    def _exists(self) -> bool:
        # TODO not sure how expensive creating an inspector is, might not want to do it for every run of this fn
        inspector: Inspector = inspect(self.database_content.database.db_engine())
        return inspector.has_table(table_name=self.name, schema=self.schema)

    def _grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.database_content.database.db_engine(),
            statements=self._grant_statements(grantee=grantee, privileges=privileges),
        )

    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.database_content.database.db_engine(),
            statements=self._revoke_statements(grantee=grantee, privileges=privileges),
        )

    @staticmethod
    def _allowed_privileges() -> set[Privilege]:
        return {
            Privilege.INSERT,
            Privilege.SELECT,
            Privilege.UPDATE,
            Privilege.DELETE,
            Privilege.TRUNCATE,
            Privilege.REFERENCES,
            Privilege.TRIGGER,
            Privilege.ALL_PRIVILEGES,
        }
