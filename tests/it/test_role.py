from datetime import datetime, timedelta

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import Engine

from dbdeclare.controller import Controller
from dbdeclare.entities.entity import Entity
from dbdeclare.entities.role import Role


def test_does_not_exist(simple_role: Role) -> None:
    assert not simple_role._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_role: Role) -> None:
    simple_role._safe_create()
    assert simple_role._exists()


@pytest.mark.order(after="test_create")
def test_grant_does_not_exist() -> None:
    pass  # assert grant doesn't exist


@pytest.mark.order(after="test_grant_does_not_exist")
def test_grant() -> None:
    pass  # assert grant exists


@pytest.mark.order(after="test_grant")
def test_revoke() -> None:
    pass  # assert grant doesn't exist


@pytest.mark.order(after="test_create")
def test_drop(simple_role: Role) -> None:
    simple_role._safe_drop()
    assert not simple_role._exists()


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
@pytest.mark.order(after="test_drop")
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
    temp_role._safe_create()
    temp_role._safe_drop()


@pytest.mark.order(after="test_drop")
def test_dependency_inputs(engine: Engine) -> None:
    existing_roles = [Role(name=f"existing_{n}") for n in range(3)]
    Role(name="in_one", in_role=(existing_roles[0],))
    Role(name="in_multiple", in_role=existing_roles)
    Role(name="has_one", role=(existing_roles[0],))
    Role(name="has_multiple", role=existing_roles)
    Role(name="admin_one", admin=(existing_roles[0],))
    Role(name="admin_multiple", admin=existing_roles)
    Controller.create_all(engine)
    Controller.drop_all(engine)
