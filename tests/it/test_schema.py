import pytest
from sqlalchemy import Engine

from postgres_declare.controller import Controller
from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.database import Database
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema


@pytest.fixture
def schema_privileges() -> set[Privilege]:
    return {Privilege.CREATE, Privilege.USAGE}


def test_does_not_exist(simple_schema: Schema, simple_db: Database) -> None:
    simple_db._safe_create()
    assert not simple_schema._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_schema: Schema) -> None:
    simple_schema._safe_create()
    assert simple_schema._exists()


@pytest.mark.order(after="test_create")
def test_grant_does_not_exist(simple_schema: Schema, grant_role: Role, schema_privileges: set[Privilege]) -> None:
    grant_role._safe_create()
    assert not simple_schema._grants_exist(grantee=grant_role, privileges=schema_privileges)


@pytest.mark.order(after="test_grant_does_not_exist")
def test_grant(simple_schema: Schema, grant_role: Role, schema_privileges: set[Privilege]) -> None:
    simple_schema.grant(grants=[GrantTo(privileges=list(schema_privileges), to=[grant_role])])
    grant_role._safe_grant()
    assert simple_schema._grants_exist(grantee=grant_role, privileges=schema_privileges)


@pytest.mark.order(after="test_grant")
def test_revoke(simple_schema: Schema, grant_role: Role, schema_privileges: set[Privilege]) -> None:
    grant_role._safe_revoke()
    assert not simple_schema._grants_exist(grantee=grant_role, privileges=schema_privileges)
    # clean up role
    grant_role._safe_drop()


@pytest.mark.order(after="test_create")
def test_drop(simple_schema: Schema, simple_db: Database) -> None:
    simple_schema._safe_drop()
    assert not simple_schema._exists()
    # clean up database
    simple_db._safe_drop()


@pytest.mark.order(after="test_drop")
def test_dependency_inputs(engine: Engine) -> None:
    Entity.entities = []
    Entity.check_if_any_exist = False
    existing_role = Role(name="existing_role_for_schema")
    existing_db = Database(name="foobar")
    Schema(name="has_owner", database=existing_db, owner=existing_role)
    Controller.create_all(engine)
    Controller.drop_all()
