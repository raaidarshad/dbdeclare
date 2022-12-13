import pytest
from sqlalchemy import Engine, create_engine

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database, Role
from tests.helpers import YieldFixture


@pytest.fixture
def test_db() -> YieldFixture[Database]:
    yield Database(name="test_db")
    Entity.entities = []
    Entity.check_if_any_exist = False


@pytest.fixture
def engine() -> Engine:
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}")


def test_does_not_exist(test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_db.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    test_db.safe_create()
    assert test_db.exists()


@pytest.mark.order(after="test_create")
def test_remove(test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    test_db.safe_remove()
    assert not test_db.exists()


def test_inputs(engine: Engine) -> None:
    # allow_connections
    # connection_limit
    # is_template
    pass


def test_specific_inputs(engine: Engine) -> None:
    # template
    pass


@pytest.mark.order(after="test_remove")
def test_dependency_inputs(engine: Engine) -> None:
    existing_role = Role(name="existing_role_for_db")
    Database(name="has_owner", owner=existing_role)
    Entity.create_all(engine)
    Entity.remove_all(engine)
