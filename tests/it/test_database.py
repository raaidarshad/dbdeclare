import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
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


@given(
    allow_connections=st.booleans(),
    connection_limit=st.integers(min_value=-1, max_value=100),
    is_template=st.booleans(),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.order(after="test_remove")
def test_inputs(allow_connections: bool, connection_limit: int, is_template: bool, engine: Engine) -> None:
    Entity._engine = engine
    temp_db = Database(
        name="bar", allow_connections=allow_connections, connection_limit=connection_limit, is_template=is_template
    )
    temp_db.safe_create()
    temp_db.safe_remove()


@pytest.mark.parametrize("template", ["template0", "template1"])
@pytest.mark.order(after="test_remove")
def test_specific_inputs(template: str, engine: Engine) -> None:
    Entity._engine = engine
    temp_db = Database(name="foobar", template=template)
    temp_db.safe_create()
    temp_db.safe_remove()


@pytest.mark.order(after="test_remove")
def test_dependency_inputs(engine: Engine) -> None:
    existing_role = Role(name="existing_role_for_db")
    Database(name="has_owner", owner=existing_role)
    Entity.create_all(engine)
    Entity.remove_all(engine)
