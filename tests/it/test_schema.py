import pytest
from sqlalchemy import Engine

from postgres_declare.entities.base_entity import Entity
from postgres_declare.entities.database import Database
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema


def test_does_not_exist(simple_schema: Schema, simple_db: Database) -> None:
    simple_db.safe_create()
    assert not simple_schema.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_schema: Schema) -> None:
    simple_schema.safe_create()
    assert simple_schema.exists()


@pytest.mark.order(after="test_create")
def test_remove(simple_schema: Schema, simple_db: Database) -> None:
    simple_schema.safe_remove()
    assert not simple_schema.exists()
    # clean up database
    simple_db.safe_remove()


@pytest.mark.order(after="test_remove")
def test_dependency_inputs(engine: Engine) -> None:
    Entity.entities = []
    Entity.check_if_any_exist = False
    existing_role = Role(name="existing_role_for_schema")
    existing_db = Database(name="foobar")
    Schema(name="has_owner", databases=[existing_db], owner=existing_role)
    Entity.create_all(engine)
    Entity.remove_all(engine)
