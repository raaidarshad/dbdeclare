from typing import Sequence

from sqlalchemy import TextClause, text

from dbdeclare.data_structures.grant_to import GrantTo
from dbdeclare.data_structures.privileges import Privilege
from dbdeclare.entities.database import Database
from dbdeclare.entities.database_entity import DatabaseSqlEntity
from dbdeclare.entities.entity import Entity
from dbdeclare.entities.role import Role
from dbdeclare.mixins.grantable import Grantable


class Schema(DatabaseSqlEntity, Grantable):
    """
    Represents a Postgres `Schema <https://www.postgresql.org/docs/15/ddl-schemas.html>`_.
    """

    def __init__(
        self,
        name: str,
        database: Database,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        owner: Role | None = None,
        grants: Sequence[GrantTo] | None = None,
    ):
        """
        All __init__ params correspond to CREATE SCHEMA arguments and options, see
        `official Postgres documentation <https://www.postgresql.org/docs/current/sql-createschema.html>`_.


        :param name: Unique name of the entity. Must be unique within a database.
        :param database: The :class:`dbdeclare.entities.Database` that this entity belongs to.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        :param owner: The :class:`dbdeclare.entitites.Role` who will own this database. Postgres defaults to the user executing the command.
        :param grants: Sequence of :class:`dbdeclare.data_structures.GrantTo` to specify privileges this database has in relation to specified roles.
        """
        self.owner = owner

        Grantable.__init__(self, name=name, grants=grants)
        DatabaseSqlEntity.__init__(
            self, name=name, depends_on=depends_on, database=database, check_if_exists=check_if_exists
        )

    def _create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE SCHEMA {self.name}"

        if self.owner:
            statement = f"{statement} AUTHORIZATION {self.owner.name}"

        return [text(statement)]

    def _exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=:schema)").bindparams(schema=self.name)

    def _drop_statements(self) -> Sequence[TextClause]:
        return [text(f"DROP SCHEMA {self.name}")]

    def _grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.database.db_engine(), statements=self._grant_statements(grantee=grantee, privileges=privileges)
        )

    def _grants_exist(self, grantee: Role, privileges: set[Privilege]) -> bool:
        rows = self._fetch_sql(engine=self.database.db_engine(), statement=self._grants_exist_statement())

        try:
            existing_privileges = list(
                filter(None, [self._extract_privileges(acl=r[0], grantee=grantee) for r in rows])
            )[0]
            return privileges.issubset(existing_privileges)
        except IndexError:
            return False

    def _grants_exist_statement(self) -> TextClause:
        """
        The SQL statement that checks to see what grants exist.
        :return: A single :class:`sqlalchemy.TextClause` containing the SQL to check what grants exist on this entity.
        """
        return text("SELECT unnest(nspacl) FROM pg_catalog.pg_namespace WHERE nspname=:schema_name").bindparams(
            schema_name=self.name
        )

    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.database.db_engine(), statements=self._revoke_statements(grantee=grantee, privileges=privileges)
        )

    @staticmethod
    def _allowed_privileges() -> set[Privilege]:
        return {Privilege.CREATE, Privilege.USAGE}
