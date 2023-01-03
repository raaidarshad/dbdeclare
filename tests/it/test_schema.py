import pytest
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.entities.database import Database
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.grant import Grant, Privilege
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema


def test_does_not_exist(simple_schema: Schema, simple_db: Database) -> None:
    simple_db._safe_create()
    assert not simple_schema._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_schema: Schema) -> None:
    simple_schema._safe_create()
    assert simple_schema._exists()


@pytest.mark.order(after="test_create")
def test_remove(simple_schema: Schema, simple_db: Database) -> None:
    simple_schema._safe_drop()
    assert not simple_schema._exists()
    # clean up database
    simple_db._safe_drop()


@pytest.mark.order(after="test_remove")
def test_dependency_inputs(engine: Engine) -> None:
    Entity.entities = []
    Entity.check_if_any_exist = False
    existing_role = Role(name="existing_role_for_schema")
    existing_db = Database(name="foobar")
    Schema(name="has_owner", databases=[existing_db], owner=existing_role)
    Base.create_all(engine)
    Base.drop_all()


@pytest.mark.parametrize(
    "privileges",
    [
        [Privilege.CREATE],
        [Privilege.USAGE],
        [Privilege.CREATE, Privilege.USAGE],
        [Privilege.ALL_PRIVILEGES],
    ],
)
@pytest.mark.order(after="test_remove")
def test_grant(privileges: list[Privilege], engine: Engine) -> None:
    Entity.entities = []
    grantees = [Role(name=f"schema_grantee_{num}") for num in range(2)]
    dbs = [Database(name=f"db_for_schema_grants_{num}") for num in range(2)]
    schema = Schema(name="schema_for_grants", databases=dbs)
    # grant
    schema.grant([Grant(privileges=privileges, grantees=grantees)])
    # execute
    Base.run_all(engine)
    # todo confirm access in place?
    # remove
    Base.drop_all(engine)
