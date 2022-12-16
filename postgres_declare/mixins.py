from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import Engine, Row, TextClause


class SQLMixin(ABC):
    @staticmethod
    def _commit_sql(engine: Engine, statements: Sequence[TextClause]) -> None:
        with engine.connect() as conn:
            for statement in statements:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)
                conn.commit()

    @staticmethod
    def _fetch_sql(engine: Engine, statement: TextClause) -> Sequence[Row[Any]]:
        with engine.connect() as conn:
            result = conn.execute(statement)
            return result.all()

    @abstractmethod
    def create_statements(self) -> Sequence[TextClause]:
        pass

    @abstractmethod
    def exists_statement(self) -> TextClause:
        pass

    @abstractmethod
    def remove_statements(self) -> Sequence[TextClause]:
        pass
