from typing import Optional

import pytest
from sqlalchemy import Engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database
from postgres_declare.database_entities import DatabaseContent
from tests.helpers import YieldFixture


class MyBase(DeclarativeBase):
    pass


class MyFirst(MyBase):
    __tablename__ = "my_first"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]


@pytest.fixture
def test_db() -> YieldFixture[Database]:
    yield Database(name="test_db_for_content")
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def test_content(test_db: Database) -> YieldFixture[DatabaseContent]:
    yield DatabaseContent(name="test_content", sqlalchemy_base=MyBase, databases=[test_db])
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


def test_does_not_exist(test_content: DatabaseContent, test_db: Database, engine: Engine) -> None:
    Entity._engine = engine
    # need the database to exist for this and the next two tests
    test_db.safe_create()
    assert not test_content.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(test_content: DatabaseContent, engine: Engine) -> None:
    Entity._engine = engine
    test_content.safe_create()
    assert test_content.exists()


@pytest.mark.order(after="test_create")
def test_remove(test_content: DatabaseContent, engine: Engine) -> None:
    Entity._engine = engine
    test_content.safe_remove()
    assert not test_content.exists()
