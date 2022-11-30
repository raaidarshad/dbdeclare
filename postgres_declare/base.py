from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Sequence, Type

from sqlalchemy import Engine, Inspector, Row, TextClause, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase

from postgres_declare.exceptions import EntityExistsError, NoEngineError


class Entity(ABC):
    entities: list["Entity"] = []
    error_if_any_exist: bool = False
    _engine: Engine | None = None

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        error_if_exists: bool | None = None,
    ):
        # TODO have "name" be a str class that validates via regex for valid postgres names
        self.name = name

        # explicit None check because False requires different behavior
        if error_if_exists is None:
            self.error_if_exists = self.__class__.error_if_any_exist
        else:
            self.error_if_exists = error_if_exists

        if not depends_on:
            depends_on = []
        self.depends_on: Sequence["Entity"] = depends_on

        self.__class__._register(self)

    @classmethod
    def _register(cls, entity: "Entity") -> None:
        cls.entities.append(entity)

    @classmethod
    def engine(cls) -> Engine:
        if cls._engine:
            return cls._engine
        else:
            raise NoEngineError(
                "There is no SQLAlchemy Engine present. `Base._engine` must have "
                "a valid engine. This should be passed via the `_create_all` method."
            )

    def safe_create(self):
        if not self.exists():
            self.create()
        else:
            if self.error_if_exists:
                raise EntityExistsError(
                    f"There is already a {self.__class__.__name__} with the "
                    f"name {self.name}. If you want to proceed anyway, set "
                    f"the `error_if_exists` parameter to False. This will "
                    f"simply skip over the existing entity."
                )
            else:
                # TODO log that we no-op?
                pass

    @abstractmethod
    def create(self) -> None:
        pass

    @classmethod
    def create_all(cls, engine: Engine) -> None:
        cls._engine = engine
        for entity in cls.entities:
            entity.safe_create()

    @abstractmethod
    def exists(self) -> bool:
        pass


class ClusterWideEntity(Entity):
    @classmethod
    def _commit_sql(cls, statement: TextClause) -> None:
        with cls.engine().connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)
            conn.commit()

    @classmethod
    def _fetch_sql(cls, statement: TextClause) -> Sequence[Row[Any]]:
        with cls.engine().connect() as conn:
            result = conn.execute(statement)
            return result.all()

    def create(self) -> None:
        self.__class__._commit_sql(self.create_statement())

    @abstractmethod
    def create_statement(self) -> TextClause:
        pass

    def exists(self) -> bool:
        rows = self.__class__._fetch_sql(self.exists_statement())
        return rows[0][0]

    @abstractmethod
    def exists_statement(self) -> TextClause:
        pass


class Database(ClusterWideEntity):
    _db_engine: Engine | None = None
    # TODO not sure if this is right or how to use these properly, keep running unto issues when I try
    literals = [
        "locale",
        "lc_collate",
        "lc_ctype",
        "icu_locale",
        "collation_version",
        "oid",
    ]

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        error_if_exists: bool | None = None,
        owner: str | None = None,
        template: str | None = None,
        encoding: str | None = None,
        strategy: str | None = None,
        locale: str | None = None,
        lc_collate: str | None = None,
        lc_ctype: str | None = None,
        icu_locale: str | None = None,
        locale_provider: str | None = None,
        collation_version: str | None = None,
        tablespace: str | None = None,
        allow_connections: bool | None = None,
        connection_limit: int | None = None,
        is_template: bool | None = None,
        oid: str | None = None,
    ):
        self.owner = owner
        self.template = template
        self.encoding = encoding
        self.strategy = strategy
        self.locale = locale
        self.lc_collate = lc_collate
        self.lc_ctype = lc_ctype
        self.icu_locale = icu_locale
        self.locale_provider = locale_provider
        self.collation_version = collation_version
        self.tablespace = tablespace
        self.allow_connections = allow_connections
        self.connection_limit = connection_limit
        self.is_template = is_template
        self.oid = oid
        super().__init__(
            name=name, depends_on=depends_on, error_if_exists=error_if_exists
        )

    def create_statement(self) -> TextClause:
        statement = f"CREATE DATABASE {self.name}"

        # grab all the arguments to __init__ that aren't in the superclass and have a non-None value
        props = {
            k: v
            for k, v in vars(self).items()
            if (k not in signature(ClusterWideEntity.__init__).parameters)
            and (v is not None)
        }

        # append the arguments to the sql statement, "bind" aka quote the ones that need to be literal values
        for k, v in props.items():
            statement = f"{statement} {k.upper()}="
            if k in self.__class__.literals:
                # bind param, "CREATE DATABASE dbname PROP=" + ":var_to_be_bound"
                statement = f"{statement}:{k}"
            else:
                # don't bind, "CREATE DATABASE dbname PROP=" + "VALUE"
                statement = f"{statement}{v}"

        bound_props = {k: v for k, v in props.items() if k in self.__class__.literals}
        return text(statement).bindparams(**bound_props)

    def exists_statement(self) -> TextClause:
        return text(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=:db)"
        ).bindparams(db=self.name)

    def db_engine(self) -> Engine:
        # database entities will reference this as the engine to use
        if not self.__class__._db_engine:
            # grab everything but db name from the cluster engine
            host = self.__class__.engine().url.host
            port = self.__class__.engine().url.port
            user = self.__class__.engine().url.username
            pw = self.__class__.engine().url.password

            # then create a new engine
            self.__class__._db_engine = create_engine(
                f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{self.name}"
            )
        return self.__class__._db_engine


class Role(ClusterWideEntity):
    pass


class DatabaseEntity(Entity):
    def __init__(
        self,
        name: str,
        databases: Sequence[Database] | None = None,
        error_if_exists: bool | None = None,
    ):
        if not databases:
            databases = []
        self.databases: Sequence[Database] = databases
        super().__init__(name=name, error_if_exists=error_if_exists)


class DatabaseContent(DatabaseEntity):
    def __init__(
        self,
        name: str,
        sqlalchemy_base: Type[DeclarativeBase],
        databases: Sequence[Database] | None = None,
        error_if_exists: bool | None = None,
    ):
        super().__init__(
            name=name, databases=databases, error_if_exists=error_if_exists
        )
        self.base = sqlalchemy_base

    def create(self) -> None:
        for db in self.databases:
            self.base.metadata.create_all(db.db_engine())

    def exists(self) -> bool:
        tables_in_db = []
        for db in self.databases:
            inspector: Inspector = inspect(db.db_engine())
            tables_in_db.append(
                all(
                    [
                        inspector.has_table(table.name)
                        for table in self.base.metadata.tables.values()
                    ]
                )
            )
        return all(tables_in_db)


class Grant(DatabaseEntity):
    pass


class Policy(DatabaseEntity):
    # have this be the thing that can enable RLS?
    pass
