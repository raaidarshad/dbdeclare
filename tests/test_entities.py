import pytest
from sqlalchemy import Engine, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.base import Database, DatabaseContent, Entity, Role
from postgres_declare.exceptions import EntityExistsError, NoEngineError


class MyBase(DeclarativeBase):
    pass


class User(MyBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))


@pytest.fixture(autouse=True)
def clean_base() -> None:
    Entity.entities = []
    Entity.error_if_any_exist = False


@pytest.fixture
def engine() -> Engine:
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}")


@pytest.fixture
def test_db() -> Database:
    return Database(
        "test",
        allow_connections=True,
        strategy="WAL_LOG",
        template="template1",
        connection_limit=4,
        encoding="UTF8",
        locale_provider="libc",
    )


@pytest.fixture
def test_tables(test_db: Database) -> DatabaseContent:
    return DatabaseContent("test_tables", sqlalchemy_base=MyBase, databases=[test_db])


@pytest.fixture
def test_role() -> Role:
    return Role("test_role")


def test_database_init(test_db: Database) -> None:
    assert test_db in Entity.entities


def test_register_order(test_db: Database) -> None:
    prod_db = Database("prod", depends_on=[test_db])

    assert Entity.entities[0] == test_db
    assert Entity.entities[1] == prod_db


def test_no_engine(test_db: Database) -> None:
    with pytest.raises(NoEngineError):
        test_db.create()
    with pytest.raises(NoEngineError):
        test_db.exists()


def test_database_content_present(test_tables: DatabaseContent) -> None:
    assert test_tables in Entity.entities


# tests that interact with postgres
def test_database_does_not_exist(test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_db.exists()


@pytest.mark.order(after="test_database_does_not_exist")
def test_database_create_if_not_exist(test_db: Database, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_db.exists()


@pytest.mark.order(after="test_database_create_if_not_exist")
def test_database_create_if_exists_no_error_flag(test_db: Database, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.order(after="test_database_create_if_exists_no_error_flag")
def test_database_create_if_exists_yes_error_flag(test_db: Database, engine: Engine) -> None:
    test_db.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


@pytest.mark.order(after="test_database_create_if_not_exist")
def test_database_content_does_not_exist(test_db: Database, test_tables: DatabaseContent, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_tables.exists()


@pytest.mark.order(after="test_database_content_does_not_all_exist")
def test_database_content_create_if_not_exist(test_tables: DatabaseContent, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_tables.exists()


@pytest.mark.order(after="test_database_content_create_if_not_exist")
def test_database_content_create_if_exists_no_error_flag(test_tables: DatabaseContent, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.order(after="test_database_content_create_if_exists_no_error_flag")
def test_database_content_create_if_exists_yes_error_flag(test_tables: DatabaseContent, engine: Engine) -> None:
    test_tables.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


def test_role_does_not_exist(test_role: Role, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_role.exists()
