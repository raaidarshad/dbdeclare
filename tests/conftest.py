from typing import Optional, Type

import pytest
from sqlalchemy import Engine, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database, Role
from postgres_declare.database_entities import DatabaseContent
from tests.helpers import YieldFixture


@pytest.fixture(scope="module")
def engine() -> Engine:
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}")


@pytest.fixture(scope="module")
def entity(engine: Engine) -> YieldFixture[Type[Entity]]:
    Entity._engine = engine
    yield Entity
    Entity.entities = []
    Entity.check_if_any_exist = False


@pytest.fixture(scope="module")
def simple_db(entity: Entity) -> YieldFixture[Database]:
    yield Database(name="simple_db")


@pytest.fixture(scope="module")
def simple_role(entity: Entity) -> YieldFixture[Role]:
    yield Role(name="simple_role")


class MyBase(DeclarativeBase):
    pass


class SimpleTable(MyBase):
    __tablename__ = "simple_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]


@pytest.fixture(scope="module")
def simple_db_for_content(entity: Entity) -> YieldFixture[Database]:
    yield Database(name="simple_db_for_content")


@pytest.fixture(scope="module")
def simple_db_content(entity: Entity, simple_db_for_content: Database) -> YieldFixture[DatabaseContent]:
    yield DatabaseContent(name="simple_db_content", databases=[simple_db_for_content], sqlalchemy_base=MyBase)
