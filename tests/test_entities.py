from datetime import datetime, timedelta

import pytest
from sqlalchemy import Engine, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.base import Database, DatabaseContent, Entity, Role
from postgres_declare.exceptions import EntityExistsError, NoEngineError

########################
# FIXTURES AND CLASSES #
########################


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
    return Role("test_role", superuser=False, createdb=True, createrole=True, connection_limit=4)


@pytest.fixture
def test_user(test_role) -> Role:
    return Role(
        "test_user",
        login=True,
        password="fakepw123",
        encrypted_password=True,
        valid_until=datetime.today() + timedelta(days=180),
        in_role=[test_role],
    )


#########
# TESTS #
#########


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


def test_get_passed_args() -> None:
    args = dict(
        name="test",
        allow_connections=True,
        strategy="WAL_LOG",
        template="template1",
        connection_limit=4,
        encoding="UTF8",
        locale_provider="libc",
    )
    new_db = Database(**args)
    check_args = new_db._get_passed_args()
    # remove "name" before check because it isn't a child class argument, so it shouldn't be in the fn output
    args.pop("name")
    assert args == check_args


############
# DB TESTS #
############


@pytest.mark.with_db
def test_database_does_not_exist(test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_db.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_database_does_not_exist")
def test_database_create_if_not_exist(test_db: Database, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_db.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_database_create_if_not_exist")
def test_database_create_if_exists_no_error_flag(test_db: Database, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.with_db
@pytest.mark.order(after="test_database_create_if_exists_no_error_flag")
def test_database_create_if_exists_yes_error_flag(test_db: Database, engine: Engine) -> None:
    test_db.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


@pytest.mark.with_db
@pytest.mark.order(after="test_database_create_if_not_exist")
def test_database_content_does_not_exist(test_db: Database, test_tables: DatabaseContent, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_tables.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_database_content_does_not_exist")
def test_database_content_create_if_not_exist(test_tables: DatabaseContent, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_tables.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_database_content_create_if_not_exist")
def test_database_content_create_if_exists_no_error_flag(test_tables: DatabaseContent, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.with_db
@pytest.mark.order(after="test_database_content_create_if_exists_no_error_flag")
def test_database_content_create_if_exists_yes_error_flag(test_tables: DatabaseContent, engine: Engine) -> None:
    test_tables.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


@pytest.mark.with_db
def test_role_does_not_exist(test_role: Role, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_role.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_role_does_not_exist")
def test_role_create_if_not_exist(test_role: Role, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_role.exists()


@pytest.mark.with_db
@pytest.mark.order(after="test_role_create_if_not_exist")
def test_role_create_if_exists_no_error_flag(test_role: Role, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.with_db
@pytest.mark.order(after="test_role_create_if_exists_no_error_flag")
def test_role_create_if_exists_yes_error_flag(test_role: Role, engine: Engine) -> None:
    test_role.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


@pytest.mark.with_db
@pytest.mark.order(after="test_role_create_if_not_exist")
def test_role_create_with_password(test_user: Role, engine: Engine) -> None:
    Entity.create_all(engine)
    assert test_user.exists()
