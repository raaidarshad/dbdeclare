from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import Engine, Row, TextClause


class SQLBase(ABC):
    @staticmethod
    def _commit_sql(engine: Engine, statements: Sequence[TextClause]) -> None:
        """
        Commits SQL statements to the database specified with the provided engine.
        :param engine: A :class:`sqlalchemy.Engine` for the target database.
        :param statements: A Sequence of :class:`sqlalchemy.TextClause` statements to commit.
        """
        with engine.connect() as conn:
            for statement in statements:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)
                conn.commit()

    @staticmethod
    def _fetch_sql(engine: Engine, statement: TextClause) -> Sequence[Row[Any]]:
        """
        Fetches results from the database specified with the provided engine.
        :param engine: A :class:`sqlalchemy.Engine` for the target database.
        :param statement: A single :class:`sqlalchemy.TextClause` statement to fetch information from the database.
        :return: A Sequence of :class:`sqlalchemy.Row` that contain the results of the query provided.
        """
        with engine.connect() as conn:
            result = conn.execute(statement)
            return result.all()


class SQLCreatable(SQLBase):
    @abstractmethod
    def _create(self) -> None:
        """
        Create this entity in the cluster.
        """
        pass

    @abstractmethod
    def _exists(self) -> bool:
        """
        Check if this entity currently exists in the cluster.
        :return: True if it exists, False if it does not.
        """
        pass

    @abstractmethod
    def _drop(self) -> None:
        """
        Drop this entity from the cluster.
        """
        pass

    @abstractmethod
    def _create_statements(self) -> Sequence[TextClause]:
        """
        The SQL statements that create this entity.
        :return: A Sequence of :class:`sqlalchemy.TextClause` containing the SQL to create this entity.
        """
        pass

    @abstractmethod
    def _exists_statement(self) -> TextClause:
        """
        The SQL statement that checks to see if this entity exists.
        :return: A single :class:`sqlalchemy.TextClause` containing the SQL to check if this entity exists.
        """
        pass

    @abstractmethod
    def _drop_statements(self) -> Sequence[TextClause]:
        """
        The SQL statements that drop this entity.
        :return: A Sequence of :class:`sqlalchemy.TextClause` containing the SQL to drop this entity.
        """
        pass
