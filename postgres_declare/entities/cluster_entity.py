from postgres_declare.entities.base_entity import Entity
from postgres_declare.mixins import SQLMixin


class ClusterSqlEntity(SQLMixin, Entity):
    def create(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self.create_statements())

    def exists(self) -> bool:
        rows = self._fetch_sql(engine=self.__class__.engine(), statement=self.exists_statement())
        return rows[0][0]  # type: ignore

    def remove(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self.remove_statements())
