from postgres_declare.entities.database import Database
from postgres_declare.entities.database_entity import DatabaseEntity
from postgres_declare.entities.entity import Entity


class MockDatabaseEntity(DatabaseEntity):
    def _create(self) -> None:
        pass

    def _exists(self) -> bool:
        pass

    def _drop(self) -> None:
        pass


def test_database_entity_hash_works(entity: Entity) -> None:
    entity.entities = []
    db1 = Database("db1")
    db2 = Database("db2")
    mde1 = MockDatabaseEntity("mde1", database=db1)
    mde2 = MockDatabaseEntity("mde1", database=db2)
    mde3 = MockDatabaseEntity("mde1", database=db1)
    myset = {mde1, mde2, mde3}
    assert len(myset) == 2


def test_database_entity_eq_works(entity: Entity) -> None:
    entity.entities = []
    db1 = Database("db1")
    db2 = Database("db2")
    mde1 = MockDatabaseEntity("mde1", database=db1)
    mde2 = MockDatabaseEntity("mde1", database=db2)
    mde3 = MockDatabaseEntity("mde1", database=db1)

    assert mde1 == mde3
    assert mde1 != mde2
