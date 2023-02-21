from dbdeclare.entities.entity import Entity
from dbdeclare.mixins.sql import SQLCreatable


class ClusterEntity(SQLCreatable, Entity):
    """
    Parent class for creatable, cluster-wide entities (like a database or role). Defines some of
    the abstract methods needed since they are consistent across entities.
    """

    def _create(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._create_statements())

    def _exists(self) -> bool:
        rows = self._fetch_sql(engine=self.__class__.engine(), statement=self._exists_statement())
        return rows[0][0]  # type: ignore

    def _drop(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._drop_statements())
