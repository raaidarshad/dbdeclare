import pytest
from sqlalchemy import create_engine

from postgres_declare.entities import Base, Database
from postgres_declare.exceptions import EntityExistsError, NoEngineError


@pytest.fixture(autouse=True)
def clean_base():
    Base.entities = []
    Base.error_if_any_exist = False


@pytest.fixture
def engine():
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(
        f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"
    )


@pytest.fixture
def test_db():
    return Database("test")


def test_database_init(test_db):
    assert test_db in Base.entities


def test_register_order(test_db):
    prod_db = Database("prod", depends_on=[test_db])

    assert Base.entities[0] == test_db
    assert Base.entities[1] == prod_db


def test_no_engine(test_db, engine):
    with pytest.raises(NoEngineError):
        test_db.create()


# tests that interact with postgres
def test_database_does_not_exist(test_db, engine):
    Base._engine = engine
    assert not test_db.exists()


@pytest.mark.order(after="test_database_does_not_exist")
def test_database_create_if_not_exist(test_db, engine):
    Base._create_all(engine)
    assert test_db.exists()


@pytest.mark.order(after="test_database_create_if_not_exist")
def test_database_create_if_exists_no_error_flag(test_db, engine):
    Base._create_all(engine)
    # should simply no op, nothing to assert really


@pytest.mark.order(after="test_database_create_if_exists_no_error_flag")
def test_database_create_if_exists_yes_error_flag(test_db, engine):
    test_db.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Base._create_all(engine)
