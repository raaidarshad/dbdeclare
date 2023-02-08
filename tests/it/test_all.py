from sqlalchemy import Engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.base import Base
from postgres_declare.data_structures import GrantOn, GrantTo, Privilege
from postgres_declare.entities import Database, DatabaseContent, Role, Schema

schema_name = "logs"


class MockBase(DeclarativeBase):
    pass


class Event(MockBase):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))


class Pipeline(MockBase):
    __tablename__ = "pipeline"
    __table_args__ = {"schema": schema_name}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))


def test_all(engine: Engine) -> None:
    for stage in ["dev", "prod"]:

        db = Database(name=stage)
        reader = Role(name=f"{stage}_reader", grants=[GrantOn(privileges=[Privilege.CONNECT], on=[db])])
        writer = Role(name=f"{stage}_writer", grants=[GrantOn(privileges=[Privilege.CONNECT], on=[db])])
        # define schemas
        logs_schema = Schema(name=schema_name, database=db)
        # define db content with grants
        db_content = DatabaseContent(name="main", sqlalchemy_base=MockBase, database=db, schemas=[logs_schema])

        db_content.tables["event"].grant(grants=[GrantTo(privileges=[Privilege.SELECT], to=[reader, writer])])
        db_content.tables["event"].grant(grants=[GrantTo(privileges=[Privilege.INSERT, Privilege.UPDATE], to=[writer])])

    # create and grant all, confirm everything exists
    Base.run_all(engine)
    assert Base._all_exist()
    Base.remove_all()
