# for a given entity, we want to test creating it with every type of input
# for test_args in possible_inputs:
#     define entity
#     create_entity
#     assert it exists
#     drop entity
#     assert it does not exist

import pytest
from sqlalchemy import Engine, create_engine

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database
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
