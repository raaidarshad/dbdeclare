from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dbdeclare.controller import Controller
from dbdeclare.data_structures import GrantOn, Privilege
from dbdeclare.entities import Database, DatabaseContent, Role, Schema


class ExampleBase(DeclarativeBase):
    pass


class Article(ExampleBase):
    __tablename__ = "article"
    id: Mapped[int] = mapped_column(primary_key=True)


class Keyword(ExampleBase):
    __tablename__ = "keyword"
    id: Mapped[int] = mapped_column(primary_key=True)


class Cluster(ExampleBase):
    __tablename__ = "cluster"
    id: Mapped[int] = mapped_column(primary_key=True)


class BadRequest(ExampleBase):
    __tablename__ = "bad_request"
    __table_args__ = {"schema": "log"}
    id: Mapped[int] = mapped_column(primary_key=True)


class GoodRequest(ExampleBase):
    __tablename__ = "good_request"
    __table_args__ = {"schema": "log"}
    id: Mapped[int] = mapped_column(primary_key=True)


def declare_stage(stage: str) -> None:
    db = Database(name=stage)

    # "groups" aka non-login roles
    etl_writer = Role(name=f"{stage}_etl_writer")
    ml_writer = Role(name=f"{stage}_ml_writer")
    reader = Role(name=f"{stage}_reader")

    # "users" aka login roles
    Role(name=f"{stage}_etl", login=True, password="fake", in_role=[etl_writer, reader])
    Role(name=f"{stage}_ml", login=True, password="fake", in_role=[ml_writer, reader])

    # create extra schemas
    log_schema = Schema(name="log", database=db)

    # create db content
    content = DatabaseContent(name="main", database=db, sqlalchemy_base=ExampleBase, schemas=[log_schema])

    # grant privileges
    etl_writer.grant(
        grants=[
            GrantOn(
                privileges=[Privilege.INSERT, Privilege.UPDATE],
                on=[content.tables[Article.__tablename__], content.tables[Keyword.__tablename__]],
            )
        ]
    )
    ml_writer.grant(
        grants=[GrantOn(privileges=[Privilege.INSERT, Privilege.UPDATE], on=[content.tables[Cluster.__tablename__]])]
    )
    reader.grant(
        grants=[
            GrantOn(
                privileges=[Privilege.SELECT],
                on=[
                    content.tables[Article.__tablename__],
                    content.tables[Keyword.__tablename__],
                    content.tables[Cluster.__tablename__],
                ],
            )
        ]
    )

    # create log role and grant privileges if not test stage
    if stage != "test":
        log_role = Role(
            name=f"{stage}_logger",
            grants=[
                GrantOn(privileges=[Privilege.USAGE], on=[log_schema]),
                GrantOn(
                    privileges=[Privilege.INSERT, Privilege.SELECT, Privilege.UPDATE],
                    on=[content.tables[BadRequest.__tablename__], content.tables[GoodRequest.__tablename__]],
                ),
            ],
        )
        Role(name=f"{stage}_api", login=True, password="fake", in_role=[log_role, reader])


def main() -> None:
    # declare stages
    stages = ["test", "dev", "prod"]
    for stage in stages:
        declare_stage(stage)

    # create engine with admin user and default database
    engine = create_engine(url="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres")
    # create all entities and grant all privileges
    Controller.run_all(engine=engine)


if __name__ == "__main__":
    main()
