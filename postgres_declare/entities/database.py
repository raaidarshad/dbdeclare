import re
from typing import Sequence

from sqlalchemy import Engine, TextClause, create_engine, text

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.cluster_entity import ClusterEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.mixins.grantable import Grantable


class Database(ClusterEntity, Grantable):
    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        owner: Role | None = None,
        template: str | None = None,
        # encoding: str | None = None,
        # strategy: str | None = None,
        # locale: str | None = None,
        # lc_collate: str | None = None,
        # lc_ctype: str | None = None,
        # icu_locale: str | None = None,
        # locale_provider: str | None = None,
        # collation_version: str | None = None,
        # tablespace: str | None = None,
        allow_connections: bool | None = None,
        connection_limit: int | None = None,
        is_template: bool | None = None,
        # oid: str | None = None,
        grants: Sequence[GrantTo] | None = None,
    ):
        self.owner = owner
        self.template = template
        # self.encoding = encoding
        # self.strategy = strategy
        # self.locale = locale
        # self.lc_collate = lc_collate
        # self.lc_ctype = lc_ctype
        # self.icu_locale = icu_locale
        # self.locale_provider = locale_provider
        # self.collation_version = collation_version
        # self.tablespace = tablespace
        self.allow_connections = allow_connections
        self.connection_limit = connection_limit
        self.is_template = is_template
        # self.oid = oid

        self._db_engine: Engine | None = None

        Grantable.__init__(self, name=name, grants=grants)
        ClusterEntity.__init__(self, name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def _create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE DATABASE {self.name}"

        props = self._get_passed_args()

        # append the arguments to the sql statement
        for k, v in props.items():
            # case owner and type Role, use role.name
            match k, v:
                case "owner", v:
                    statement = f"{statement} OWNER={v.name}"
                case "grants", _:
                    pass
                case k, v:
                    statement = f"{statement} {k.upper()}={v}"

        return [text(statement)]

    def _exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=:db)").bindparams(db=self.name)

    def _drop_statements(self) -> Sequence[TextClause]:
        statements = []
        if self.is_template:
            # cannot drop a template, must set is_template to false before drop
            statements.append(text(f"ALTER DATABASE {self.name} is_template false"))
        statements.append(text(f"DROP DATABASE {self.name} (FORCE)"))
        return statements

    def _grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.engine(), statements=self._grant_statements(grantee=grantee, privileges=privileges)
        )

    def _grants_exist(self, grantee: Role, privileges: set[Privilege]) -> bool:
        rows = self._fetch_sql(engine=self.engine(), statement=self._grants_exist_statement())
        # filter to grantee and extract privileges
        try:
            existing_privileges = list(
                filter(None, [self._extract_privileges(acl=r[0], grantee=grantee) for r in rows])
            )[0]
            return privileges.issubset(existing_privileges)
        except IndexError:
            return False

    def _extract_privileges(self, acl: str, grantee: Role) -> set[Privilege]:
        m = re.match(r"(\w*)=(\w*)\/(\w*)", acl)
        if m:
            if m.group(1) == grantee.name:
                raw_privileges = m.group(2)
                return {self._code_to_privilege(code) for code in raw_privileges}
        return set()

    def _grants_exist_statement(self) -> TextClause:
        return text("SELECT unnest(datacl) as acl FROM pg_catalog.pg_database WHERE datname=:db_name").bindparams(
            db_name=self.name
        )

    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        self._commit_sql(
            engine=self.engine(), statements=self._revoke_statements(grantee=grantee, privileges=privileges)
        )

    @staticmethod
    def _allowed_privileges() -> set[Privilege]:
        return {Privilege.CREATE, Privilege.CONNECT, Privilege.TEMPORARY, Privilege.ALL_PRIVILEGES}

    def db_engine(self) -> Engine:
        # database entities will reference this as the engine to use
        if not self._db_engine:
            # grab everything but db name from the cluster engine
            host = self.__class__.engine().url.host
            port = self.__class__.engine().url.port
            user = self.__class__.engine().url.username
            pw = self.__class__.engine().url.password

            # then create a new engine
            self._db_engine = create_engine(f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{self.name}")
        return self._db_engine
