from typing import Sequence, Type

from sqlalchemy import Inspector, inspect
from sqlalchemy.orm import DeclarativeBase

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database


class DatabaseEntity(Entity):
    def __init__(
        self,
        name: str,
        databases: Sequence[Database],
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        self.databases: Sequence[Database] = databases
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)


class DatabaseContent(DatabaseEntity):
    def __init__(
        self,
        name: str,
        sqlalchemy_base: Type[DeclarativeBase],
        databases: Sequence[Database],
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        super().__init__(name=name, depends_on=depends_on, databases=databases, check_if_exists=check_if_exists)
        self.base = sqlalchemy_base

    def create(self) -> None:
        for db in self.databases:
            self.base.metadata.create_all(db.db_engine())

    def exists(self) -> bool:
        tables_in_db = []
        for db in self.databases:
            inspector: Inspector = inspect(db.db_engine())
            tables_in_db.append(all([inspector.has_table(table.name) for table in self.base.metadata.tables.values()]))
        return all(tables_in_db)

    def remove(self) -> None:
        for db in self.databases:
            self.base.metadata.drop_all(db.db_engine())


class Grant(DatabaseEntity):
    pass


class Policy(DatabaseEntity):
    # have this be the thing that can enable RLS?
    pass
