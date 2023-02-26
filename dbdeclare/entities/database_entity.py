from typing import Sequence

from dbdeclare.entities.database import Database
from dbdeclare.entities.entity import Entity
from dbdeclare.mixins.sql import SQLCreatable


class DatabaseEntity(Entity):
    """
    Parent class for database-wide entities (most everything that isn't a database or role).
    """

    def __init__(
        self,
        name: str,
        database: Database,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        """
        :param name: Unique name of the entity. Cluster-level entities must be unique, database-level entities must be unique within a database.
        :param database: The :class:`dbdeclare.entities.Database` that this entity belongs to.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        """
        self.database = database
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def __hash__(self) -> int:
        return hash((self.name, self.__class__.__name__, self.database.name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.name, self.__class__.__name__, self.database.name) == (
            other.name,
            other.__class__.__name__,
            other.database.name,
        )


class DatabaseSqlEntity(SQLCreatable, DatabaseEntity):
    """
    Parent class for creatable, database-wide entities. Defines some of the abstract methods needed since they are
    consistent across entities.
    """

    def _create(self) -> None:
        self._commit_sql(engine=self.database.db_engine(), statements=self._create_statements())

    def _exists(self) -> bool:
        rows = self._fetch_sql(engine=self.database.db_engine(), statement=self._exists_statement())
        return rows[0][0]  # type: ignore

    def _drop(self) -> None:
        self._commit_sql(engine=self.database.db_engine(), statements=self._drop_statements())
