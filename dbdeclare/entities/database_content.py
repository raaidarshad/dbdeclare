from __future__ import annotations

from typing import Sequence, Type

from sqlalchemy import Inspector, TextClause, inspect, text
from sqlalchemy.orm import DeclarativeBase

from dbdeclare.data_structures.grant_to import GrantTo
from dbdeclare.data_structures.privileges import Privilege
from dbdeclare.entities.database import Database
from dbdeclare.entities.database_entity import DatabaseEntity
from dbdeclare.entities.entity import Entity
from dbdeclare.entities.role import Role
from dbdeclare.entities.schema import Schema
from dbdeclare.mixins.grantable import Grantable
from dbdeclare.mixins.sql import SQLBase


class DatabaseContent(DatabaseEntity):
    """
    Represents a `sqlalchemy.orm.DeclarativeBase` and other helpful functionality.
    """

    def __init__(
        self,
        name: str,
        sqlalchemy_base: Type[DeclarativeBase],
        database: Database,
        schemas: Sequence[Schema] | None = None,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        """
        :param name: Unique name of the entity. Must be unique within a database.
        :param sqlalchemy_base: The `sqlalchemy.orm.DeclarativeBase` to refer to a collection of tables.
        :param schemas: Any schemas that need to be created prior to the tables specified in the sqlalchemy_base.
        :param database: The :class:`dbdeclare.entities.Database` that this entity belongs to.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        """
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
    """
    An internal wrapper for a table, primarily intended to allow easy access to grants.
    """

    def __init__(self, name: str, database_content: DatabaseContent, schema: str | None = "public"):
        """
        :param name: Unique name of the entity. Must be unique within a schema within a database.
        :param database_content: The `dbdeclare.entities.DatabaseContent` this Table belongs to.
        :param schema: The string name of the schema this belongs to.
        """
        super().__init__(name=name)

        if schema:
            self._grant_name = f"{schema}.{name}"

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

    def _grants_exist(self, grantee: Role, privileges: set[Privilege]) -> bool:
        rows = self._fetch_sql(
            engine=self.database_content.database.db_engine(), statement=self._grants_exist_statement(grantee=grantee)
        )
        existing_privileges = {r[0] for r in rows}
        return self._check_privileges(declared_privileges=privileges, existing_privileges=existing_privileges)

    def _grants_exist_statement(self, grantee: Role) -> TextClause:
        """
        The SQL statement that checks to see what grants exist.
        :return: A single :class:`sqlalchemy.TextClause` containing the SQL to check what grants exist on this entity.
        """
        return text(
            "SELECT privilege_type FROM information_schema.table_privileges WHERE table_name=:table_name  AND grantee=:grantee_name"
        ).bindparams(table_name=self.name, grantee_name=grantee.name)

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
