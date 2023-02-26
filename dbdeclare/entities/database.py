from typing import Sequence

from sqlalchemy import Engine, TextClause, create_engine, text

from dbdeclare.data_structures.grant_to import GrantTo
from dbdeclare.data_structures.privileges import Privilege
from dbdeclare.entities.cluster_entity import ClusterEntity
from dbdeclare.entities.entity import Entity
from dbdeclare.entities.role import Role
from dbdeclare.mixins.grantable import Grantable


class Database(ClusterEntity, Grantable):
    """
    Represents a Postgres `Database <https://www.postgresql.org/docs/current/managing-databases.html>`_.
    """

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
        """
        All __init__ params correspond to CREATE DATABASE arguments and options, see
        `official Postgres documentation <https://www.postgresql.org/docs/current/sql-createdatabase.html>`_.


        :param name: Unique name of the Database. Must be unique across the cluster.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        :param owner: The :class:`dbdeclare.entitites.Role` who will own this database. Postgres defaults to the user executing the command.
        :param template: The name of the template from which to create the new database. Postgres defaults to template1.
        :param allow_connections: Flag to allow connections to this database. Postgres defaults to `True`.
        :param connection_limit: Number of concurrent connections that can be made to this database. Postgres defaults to -1, which means no limit.
        :param is_template: Flag to allow this database to be cloned by any user with CREATEDB privileges; if `False` (the default), then only superusers or the owner of the database can clone it.
        :param grants: Sequence of :class:`dbdeclare.data_structures.GrantTo` to specify privileges this database has in relation to specified roles.
        """
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

    def _grants_exist_statement(self) -> TextClause:
        """
        The SQL statement that checks to see what grants exist.
        :return: A single :class:`sqlalchemy.TextClause` containing the SQL to check what grants exist on this entity.
        """
        return text("SELECT unnest(datacl) AS acl FROM pg_catalog.pg_database WHERE datname=:db_name").bindparams(
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
        """
        Getter for this database's engine. Will create it if it is not yet set.
        :return: A `sqlalchemy.Engine` to connect to this database.
        """
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
