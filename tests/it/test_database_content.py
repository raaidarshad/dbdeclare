import pytest

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.database import Database
from postgres_declare.entities.database_content import DatabaseContent
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema
from tests.conftest import SimpleTable


@pytest.fixture
def table_privileges() -> set[Privilege]:
    return {Privilege.SELECT, Privilege.INSERT}


def test_does_not_exist(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    # need the database to exist for this and the next two tests
    simple_db._safe_create()
    assert not simple_db_content._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_db_content: DatabaseContent, simple_schema: Schema) -> None:
    # need the schema to exist for this and the next test
    simple_schema._safe_create()
    simple_db_content._safe_create()
    assert simple_db_content._exists()


@pytest.mark.order(after="test_create")
def test_table_grant_does_not_exist(
    simple_db_content: DatabaseContent, grant_role: Role, table_privileges: set[Privilege]
) -> None:
    grant_role._safe_create()
    assert not simple_db_content.tables[SimpleTable.__tablename__]._grants_exist(
        grantee=grant_role, privileges=table_privileges
    )


@pytest.mark.order(after="test_table_grant_does_not_exist")
def test_table_grant(simple_db_content: DatabaseContent, grant_role: Role, table_privileges: set[Privilege]) -> None:
    simple_db_content.tables[SimpleTable.__tablename__].grant(
        grants=[GrantTo(privileges=list(table_privileges), to=[grant_role])]
    )
    grant_role._safe_grant()
    assert simple_db_content.tables[SimpleTable.__tablename__]._grants_exist(
        grantee=grant_role, privileges=table_privileges
    )


@pytest.mark.order(after="test_table_grant")
def test_table_revoke(simple_db_content: DatabaseContent, grant_role: Role, table_privileges: set[Privilege]) -> None:
    grant_role._safe_revoke()
    assert not simple_db_content.tables[SimpleTable.__tablename__]._grants_exist(
        grantee=grant_role, privileges=table_privileges
    )
    # clean up role
    grant_role._safe_drop()


@pytest.mark.order(after="test_table_revoke")
def test_column_grant_does_not_exist() -> None:
    # TODO
    pass


@pytest.mark.order(after="test_column_grant_does_not_exist")
def test_column_grant() -> None:
    # TODO
    pass


@pytest.mark.order(after="test_column_grant")
def test_column_revoke() -> None:
    # TODO
    pass


@pytest.mark.order(after="test_column_revoke")
def test_drop(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    simple_db_content._safe_drop()
    assert not simple_db_content._exists()
    # clean up database
    simple_db._safe_drop()
