from abc import ABC, abstractmethod
from typing import Any, Sequence

import psycopg
from sqlalchemy import Engine, Row, TextClause


class Base(ABC):
    entities: list["Base"] = []
    error_if_any_exist: bool = False
    engine: Engine | None = None

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Base"] | None = None,
        error_if_exists: bool | None = None,
    ):
        # TODO have "name" be a str class that validates via regex for valid postgres names
        self.name = name
        if not depends_on:
            depends_on = []
        # explicit None check because False requires different behavior
        if error_if_exists is None:
            self.error_if_exists = self.__class__.error_if_any_exist
        else:
            self.error_if_exists = error_if_exists
        self.depends_on = depends_on

        self.__class__._register(self)

    @classmethod
    def _register(cls, entity: "Base") -> None:
        cls.entities.append(entity)

    @classmethod
    def _create_all(cls, engine: Engine) -> None:
        cls.engine = engine
        for entity in cls.entities:
            entity.create()

    @staticmethod
    def connection() -> psycopg.Connection[Any]:
        return psycopg.connect("todo conn string")

    def commit_sql(self, statement: TextClause) -> None:
        if self.engine:
            with self.engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)
                conn.commit()
        else:
            # TODO raise specific exception
            raise Exception

    def fetch_sql(self, statement: TextClause) -> Sequence[Row[Any]]:
        if self.engine:
            with self.engine.connect() as conn:
                result = conn.execute(statement)
                return result.all()
        else:
            # TODO raise specific exception
            raise Exception

    def create(self) -> None:
        if not self.exists():
            self.commit_sql(self.create_statement())
        else:
            if self.error_if_exists:
                # TODO find or define specific exception for "entity already exists"
                raise Exception
            else:
                # TODO log that we no-op?
                pass

    @abstractmethod
    def create_statement(self) -> TextClause:
        pass

    def exists(self) -> bool:
        # this expects to receive either 0 rows or 1 row
        # if 0 rows, does not exist; if 1 row, exists; if more, something went wrong
        rows = self.fetch_sql(self.exists_statement())
        if not rows:
            return False
        if len(rows) == 1:
            return True
        else:
            # TODO probably raise some error or warning?
            return False

    @abstractmethod
    def exists_statement(self) -> TextClause:
        pass
