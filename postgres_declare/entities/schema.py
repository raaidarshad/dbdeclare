from typing import Sequence

from sqlalchemy import TextClause, text

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.database import Database
from postgres_declare.entities.database_entity import DatabaseSqlEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.mixins.grantable import Grantable


class Schema(DatabaseSqlEntity, Grantable):
    def __init__(
        self,
        name: str,
        database: Database,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        owner: Role | None = None,
        grants: Sequence[GrantTo] | None = None,
    ):
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
        pass

    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.database.db_engine(), statements=self._revoke_statements(grantee=grantee, privileges=privileges)
        )

    @staticmethod
    def _allowed_privileges() -> set[Privilege]:
        return {Privilege.CREATE, Privilege.USAGE}
