from postgres_declare.cluster_entities import Database
from postgres_declare.database_entities import Schema


def test_does_not_exist(simple_schema: Schema, simple_db: Database) -> None:
    simple_db.safe_create()
    assert not simple_schema.exists()
