from typing import Sequence

import pytest
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.exceptions import EntityExistsError, InvalidPrivilegeError
from postgres_declare.mixins.grantable import Grantable
from tests.helpers import YieldFixture


class MockGrantable(Grantable):
    def __init__(self, name: str, grants: Sequence[GrantTo] | None = None, mock_exists: bool = True):
        Grantable.__init__(self, name=name, grants=grants)
        self.mock_exists = mock_exists

    def _exists(self) -> bool:
        return self.mock_exists

    def _grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        pass

    def _grants_exist(self, grantee: Role, privileges: set[Privilege]) -> bool:
        return self.mock_exists

    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        pass

    @staticmethod
    def _allowed_privileges() -> set[Privilege]:
        return {Privilege.SELECT, Privilege.INSERT, Privilege.UPDATE, Privilege.DELETE, Privilege.ALL_PRIVILEGES}


class MockGrantableEntity(MockGrantable, Entity):
    def __init__(self, name: str, grants: Sequence[GrantTo] | None = None, mock_exists: bool = True):
        MockGrantable.__init__(self, name=name, grants=grants, mock_exists=mock_exists)
        Entity.__init__(self, name=name)

    def _create(self) -> None:
        pass

    def _drop(self) -> None:
        pass


class MockRole(Role):
    def __init__(self, name: str, mock_exists: bool = True):
        super().__init__(name=name)
        self.mock_exists = mock_exists

    def _exists(self) -> bool:
        return self.mock_exists


@pytest.fixture
def grantable() -> YieldFixture[MockGrantable]:
    yield MockGrantable(name="mock_grantable_single")
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def grantable_entity() -> YieldFixture[MockGrantableEntity]:
    yield MockGrantableEntity(name="mock_grantable_entity_single")
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def mock_role() -> YieldFixture[MockRole]:
    yield MockRole(name="mock_role", mock_exists=True)


@pytest.fixture
def mock_role_does_not_exist() -> YieldFixture[MockRole]:
    yield MockRole(name="nothere", mock_exists=False)


@pytest.fixture
def grantable_does_not_exist(mock_role: MockRole) -> YieldFixture[MockGrantable]:
    mg = MockGrantable(name="mock_grantable_does_not_exist", mock_exists=False)
    mg.grant(grants=[GrantTo(privileges=[Privilege.SELECT], to=[mock_role])])
    yield mg
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def simple_grant(mock_role: MockRole) -> YieldFixture[GrantTo]:
    yield GrantTo(privileges=[Privilege.SELECT, Privilege.INSERT], to=[mock_role])


@pytest.fixture
def invalid_grant(mock_role: MockRole) -> YieldFixture[GrantTo]:
    yield GrantTo(privileges=[Privilege.CONNECT], to=[mock_role])


@pytest.fixture
def grantable_with_grant(grantable: MockGrantable, simple_grant: GrantTo) -> YieldFixture[MockGrantable]:
    grantable.grant([simple_grant])
    yield grantable


@pytest.fixture
def grantable_with_grant_to_nonexistent_grantees(
    grantable: MockGrantable, mock_role_does_not_exist: MockRole
) -> YieldFixture[MockGrantable]:
    grant_with_nonexistent_grantees = GrantTo(privileges=[Privilege.SELECT], to=[mock_role_does_not_exist])
    grantable.grant([grant_with_nonexistent_grantees])
    yield grantable


def test_grant(grantable: MockGrantable, mock_role: MockRole, simple_grant: GrantTo) -> None:
    grantable.grant([simple_grant])
    assert mock_role.grants[grantable] == set(simple_grant.privileges)


def test_invalid_grant(grantable: MockGrantable, mock_role: MockRole, invalid_grant: GrantTo) -> None:
    with pytest.raises(InvalidPrivilegeError):
        grantable.grant([invalid_grant])


def test_order_fixing(grantable_entity: MockGrantableEntity, mock_role: MockRole, simple_grant: GrantTo) -> None:
    assert mock_role == grantable_entity.entities[1]
    assert grantable_entity == grantable_entity.entities[0]
    grantable_entity._fix_entity_order(grants=[simple_grant], target_entity=grantable_entity)
    assert mock_role == grantable_entity.entities[0]
    assert grantable_entity == grantable_entity.entities[1]


def test_grant_all(grantable_with_grant: MockGrantable, engine: Engine) -> None:
    Base.grant_all(engine)


def test_grant_all_error_if_self_does_not_exist(grantable_does_not_exist: MockGrantable, engine: Engine) -> None:
    with pytest.raises(EntityExistsError):
        Base.grant_all(engine)


def test_grant_all_error_if_targets_do_not_exist(
    grantable_with_grant_to_nonexistent_grantees: MockGrantable, engine: Engine
) -> None:
    with pytest.raises(EntityExistsError):
        Base.grant_all(engine)


def test_revoke_all(grantable_with_grant: MockGrantable, engine: Engine) -> None:
    Base.revoke_all(engine)


def test_revoke_error_if_self_does_not_exist(grantable_does_not_exist: MockGrantable, engine: Engine) -> None:
    with pytest.raises(EntityExistsError):
        Base.revoke_all(engine)


def test_revoke_error_if_targets_do_not_exist(
    grantable_with_grant_to_nonexistent_grantees: MockGrantable, engine: Engine
) -> None:
    with pytest.raises(EntityExistsError):
        Base.revoke_all(engine)
