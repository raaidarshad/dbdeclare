from sqlalchemy.orm import DeclarativeBase

from dbdeclare.data_structures import GrantOn, Privilege
from dbdeclare.entities import Database, DatabaseContent, Role, Schema


class ExampleBase(DeclarativeBase):
    pass


class Article(ExampleBase):
    __tablename__ = "article"
    pass


class Keyword(ExampleBase):
    __tablename__ = "keyword"
    pass


class Cluster(ExampleBase):
    __tablename__ = "cluster"
    pass


class BadRequest(ExampleBase):
    __tablename__ = "bad_request"
    __table_args__ = {"schema": "log"}
    pass


class GoodRequest(ExampleBase):
    __tablename__ = "good_request"
    __table_args__ = {"schema": "log"}
    pass


def create_stage(stage: str) -> None:
    # database
    db = Database(name=stage)

    # roles
    etl_writer = Role(name=f"{stage}_etl_writer")
    ml_writer = Role(name=f"{stage}_ml_writer")
    reader = Role(name=f"{stage}_reader")

    # users
    Role(name=f"{stage}_etl", in_role=[etl_writer, reader])
    Role(name=f"{stage}_ml", in_role=[ml_writer, reader])

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

    # create log role and grant privileges if dev or prod
    if stage != "test":
        log_role = Role(
            name=f"{stage}_logger",
            grants=[
                GrantOn(
                    privileges=[Privilege.INSERT, Privilege.SELECT, Privilege.UPDATE],
                    on=[content.tables[BadRequest.__tablename__], content.tables[GoodRequest.__tablename__]],
                )
            ],
        )
        Role(name=f"{stage}_api", in_role=[log_role, reader])


def main() -> None:
    stages = ["test", "dev", "prod"]
    for stage in stages:
        create_stage(stage)
