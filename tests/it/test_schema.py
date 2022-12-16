import pytest

from postgres_declare.cluster_entities import Database
from postgres_declare.database_entities import Schema


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
