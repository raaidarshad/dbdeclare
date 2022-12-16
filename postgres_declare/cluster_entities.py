from datetime import datetime
from typing import Sequence

from sqlalchemy import Engine, TextClause, create_engine, text

from postgres_declare.base_entity import Entity
from postgres_declare.mixins import SQLMixin


class ClusterSqlEntity(SQLMixin, Entity):
    def create(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self.create_statements())

    def exists(self) -> bool:
        rows = self._fetch_sql(engine=self.__class__.engine(), statement=self.exists_statement())
        return rows[0][0]  # type: ignore

    def remove(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self.remove_statements())


class Role(ClusterSqlEntity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        superuser: bool | None = None,
        createdb: bool | None = None,
        createrole: bool | None = None,
        inherit: bool | None = None,
        login: bool | None = None,
        replication: bool | None = None,
        bypassrls: bool | None = None,
        connection_limit: int | None = None,
        password: str | None = None,
        encrypted: bool | None = None,
        valid_until: datetime | None = None,
        in_role: Sequence["Role"] | None = None,
        role: Sequence["Role"] | None = None,
        admin: Sequence["Role"] | None = None,
    ):
        self.superuser = superuser
        self.createdb = createdb
        self.createrole = createrole
        self.inherit = inherit
        self.login = login
        self.replication = replication
        self.bypassrls = bypassrls
        self.connection_limit = connection_limit
        self.password = password
        self.encrypted = encrypted
        self.valid_until = valid_until
        self.in_role = in_role
        self.role = role
        self.admin = admin
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE ROLE {self.name}"
        props = self._get_passed_args()

        for k, v in props.items():
            match k, v:
                case "password", str(v):
                    if "encrypted" in props:
                        statement = f"{statement} ENCRYPTED"
                    statement = f"{statement} PASSWORD '{v}'"
                    if "valid_until" in props:
                        timestamp = props.get("valid_until")
                        statement = f"{statement} VALID UNTIL '{timestamp}'"

                case k, bool(v) if k != "encrypted":
                    flag = k.upper()
                    if not v:
                        flag = f"NO{flag}"
                    statement = f"{statement} {flag}"

                case "connection_limit", int(v):
                    statement = f"{statement} CONNECTION LIMIT {v}"

                # match a sequence with at least one element to filter out empty sequence
                case k, [first, *roles]:
                    option = k.upper().replace("_", " ")
                    roles = [first] + roles
                    formatted_roles = ", ".join([r.name for r in roles])
                    statement = f"{statement} {option} {formatted_roles}"

        # TODO binding isn't working, switching to simple quotes for now
        return [text(statement)]

    def exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_authid WHERE rolname=:role)").bindparams(role=self.name)

    def remove_statements(self) -> Sequence[TextClause]:
        return [text(f"DROP ROLE {self.name}")]


class Database(ClusterSqlEntity):
    _db_engine: Engine | None = None

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
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE DATABASE {self.name}"

        props = self._get_passed_args()

        # append the arguments to the sql statement
        for k, v in props.items():
            # case owner and type Role, use role.name
            match k, v:
                case "owner", v:
                    statement = f"{statement} OWNER={v.name}"
                case k, v:
                    statement = f"{statement} {k.upper()}={v}"

        return [text(statement)]

    def exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=:db)").bindparams(db=self.name)

    def remove_statements(self) -> Sequence[TextClause]:
        statements = []
        if self.is_template:
            # cannot drop a template, must set is_template to false before drop
            statements.append(text(f"ALTER DATABASE {self.name} is_template false"))
        statements.append(text(f"DROP DATABASE {self.name} (FORCE)"))
        return statements

    def db_engine(self) -> Engine:
        # database entities will reference this as the engine to use
        if not self.__class__._db_engine:
            # grab everything but db name from the cluster engine
            host = self.__class__.engine().url.host
            port = self.__class__.engine().url.port
            user = self.__class__.engine().url.username
            pw = self.__class__.engine().url.password

            # then create a new engine
            self.__class__._db_engine = create_engine(f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{self.name}")
        return self.__class__._db_engine
