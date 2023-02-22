from sqlalchemy import create_engine

from dbdeclare.controller import Controller
from dbdeclare.data_structures import GrantOn, Privilege
from dbdeclare.entities import Database, Role


def main() -> None:
    # define the database
    falafel_db = Database(name="falafel")
    # define the user
    Role(
        name="hungry_user",
        login=True,  # (1)!
        password="fakepassword",  # (2)!
        grants=[GrantOn(privileges=[Privilege.CONNECT], on=[falafel_db])],  # (3)!
    )

    # create engine with admin user and default database
    engine = create_engine(url="postgresql+psycopg://postgres:postgres@127.0.0.1:5433/postgres")  # (4)!
    # create all entities and grant all privileges
    Controller.run_all(engine=engine)


if __name__ == "__main__":
    main()
