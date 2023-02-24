from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
    DatabaseContent(name="main", database=db, sqlalchemy_base=ExampleBase, schemas=[log_schema])

    # create log role and grant privileges if not test stage
    if stage != "test":
        log_role = Role(name=f"{stage}_logger")
        Role(name=f"{stage}_api", login=True, password="fake", in_role=[log_role, reader])


def main() -> None:
    stages = ["test", "dev", "prod"]
    for stage in stages:
        declare_stage(stage)


if __name__ == "__main__":
    main()
