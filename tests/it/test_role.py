from datetime import datetime, timedelta

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import Engine, create_engine

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Role
from tests.helpers import YieldFixture


@pytest.fixture
def test_role() -> YieldFixture[Role]:
    yield Role(name="test_role")
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


def test_does_not_exist(test_role: Role, engine: Engine) -> None:
    Entity._engine = engine
    assert not test_role.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(test_role: Role, engine: Engine) -> None:
    Entity._engine = engine
    test_role.safe_create()
    assert test_role.exists()


@pytest.mark.order(after="test_create")
def test_remove(test_role: Role, engine: Engine) -> None:
    Entity._engine = engine
    test_role.safe_remove()
    assert not test_role.exists()


@given(
    superuser=st.booleans(),
    createdb=st.booleans(),
    createrole=st.booleans(),
    inherit=st.booleans(),
    login=st.booleans(),
    replication=st.booleans(),
    bypassrls=st.booleans(),
    connection_limit=st.integers(min_value=-1, max_value=100),
    password=st.text(min_size=3, max_size=20, alphabet=st.characters(blacklist_categories=("C", "Po"))),
    encrypted=st.booleans(),
    valid_until=st.datetimes(min_value=datetime.today(), max_value=datetime.today() + timedelta(days=180)),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.order(after="test_remove")
def test_inputs(
    superuser: bool,
    createdb: bool,
    createrole: bool,
    inherit: bool,
    login: bool,
    replication: bool,
    bypassrls: bool,
    connection_limit: int,
    password: str,
    encrypted: bool,
    valid_until: datetime,
    engine: Engine,
) -> None:
    Entity._engine = engine
    temp_role = Role(
        name="foo",
        superuser=superuser,
        createdb=createdb,
        createrole=createrole,
        inherit=inherit,
        login=login,
        replication=replication,
        bypassrls=bypassrls,
        connection_limit=connection_limit,
        password=password,
        encrypted=encrypted,
        valid_until=valid_until,
    )
    temp_role.safe_create()
    temp_role.safe_remove()
