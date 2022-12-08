import pytest
from sqlalchemy import Engine, create_engine

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Role
from tests.helpers import YieldFixture


@pytest.fixture
def test_db() -> YieldFixture[Role]:
    yield Role(name="test_db")
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


def test_does_not_exist(test_db: Role, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_db.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(test_db: Role, engine: Engine) -> None:
    Entity._engine = engine
    test_db.safe_create()
    assert test_db.exists()


@pytest.mark.order(after="test_create")
def test_remove(test_db: Role, engine: Engine) -> None:
    Entity._engine = engine
    test_db.safe_remove()
    assert not test_db.exists()


# TODO test out variety of init/create options
