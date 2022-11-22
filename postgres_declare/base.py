from abc import ABC, abstractmethod
from typing import Any, Sequence

from sqlalchemy import Engine, Row, TextClause

from postgres_declare.exceptions import EntityExistsError, NoEngineError


class Base(ABC):
    entities: list["Base"] = []
    error_if_any_exist: bool = False
    _engine: Engine | None = None

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Base"] | None = None,
        error_if_exists: bool | None = None,
    ):
        # TODO have "name" be a str class that validates via regex for valid postgres names
        self.name = name
        if not depends_on:
            depends_on = []
        # explicit None check because False requires different behavior
        if error_if_exists is None:
            self.error_if_exists = self.__class__.error_if_any_exist
        else:
            self.error_if_exists = error_if_exists
        self.depends_on = depends_on

        self.__class__._register(self)

    @classmethod
    def _register(cls, entity: "Base") -> None:
        cls.entities.append(entity)

    @classmethod
    def _create_all(cls, engine: Engine) -> None:
        cls._engine = engine
        for entity in cls.entities:
            entity.create()

    @classmethod
    def engine(cls) -> Engine:
        if cls._engine:
            return cls._engine
        else:
            raise NoEngineError(
                "There is no SQLAlchemy Engine present. `Base._engine` must have "
                "a valid engine. This should be passed via the `_create_all` method."
            )

    @classmethod
    def commit_sql(cls, statement: TextClause) -> None:
        with cls.engine().connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)
            conn.commit()

    @classmethod
    def fetch_sql(cls, statement: TextClause) -> Sequence[Row[Any]]:
        with cls.engine().connect() as conn:
            result = conn.execute(statement)
            return result.all()

    def create(self) -> None:
        if not self.exists():
            self.__class__.commit_sql(self.create_statement())
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
    def create_statement(self) -> TextClause:
        pass

    def exists(self) -> bool:
        # this expects to receive either 0 rows or 1 row
        # if 0 rows, does not exist; if 1 row, exists; if more, something went wrong
        rows = self.__class__.fetch_sql(self.exists_statement())
        if not rows:
            return False
        if len(rows) == 1:
            return True
        else:
            # TODO probably raise some error or warning?
            return False

    @abstractmethod
    def exists_statement(self) -> TextClause:
        pass
