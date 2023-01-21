from typing import Sequence

from postgres_declare.entities.database import Database
from postgres_declare.entities.entity import Entity
from postgres_declare.sqlmixin import SQLMixin


class DatabaseEntity(Entity):
    def __init__(
        self,
        name: str,
        database: Database,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        self.database = database
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)


class DatabaseSqlEntity(SQLMixin, DatabaseEntity):
    # TODO maybe inherit from grantable, maybe do it per entity?
    def _create(self) -> None:
        self._commit_sql(engine=self.database.db_engine(), statements=self._create_statements())

    def _exists(self) -> bool:
        rows = self._fetch_sql(engine=self.database.db_engine(), statement=self._exists_statement())
        return rows[0][0]  # type: ignore

    def _drop(self) -> None:
        self._commit_sql(engine=self.database.db_engine(), statements=self._drop_statements())
