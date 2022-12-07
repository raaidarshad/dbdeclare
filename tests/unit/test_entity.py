from typing import Any, Generator, Sequence, TypeVar

import pytest
from sqlalchemy import Engine, create_engine

from postgres_declare.base_entity import Entity
from postgres_declare.exceptions import EntityExistsError, NoEngineError

########################
# FIXTURES AND CLASSES #
########################

# for a given entity, we want to test creating it with every type of input
# for test_args in possible_inputs:
#     define entity
#     create_entity
#     assert it exists
#     drop entity
#     assert it does not exist


T = TypeVar("T")
YieldFixture = Generator[T, None, None]


class MockEntity(Entity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        error_if_exists: bool | None = None,
        mock_exists: bool = True,
        mock_kwarg_1: str | None = None,
        mock_kwarg_2: str | None = None,
    ):
        self.mock_exists = mock_exists
        self.mock_kwarg_1 = mock_kwarg_1
        self.mock_kwarg_2 = mock_kwarg_2
        super().__init__(name=name, depends_on=depends_on, error_if_exists=error_if_exists)

    def create(self) -> None:
        self.engine()

    def exists(self) -> bool:
        self.engine()
        return self.mock_exists


class ChildMockEntity(MockEntity):
    def __init__(self, mock_kwarg_3: str | None = None, mock_kwarg_4: str | None = None, *args: Any, **kwargs: Any):
        self.mock_kwarg_3 = mock_kwarg_3
        self.mock_kwarg_4 = mock_kwarg_4
        super().__init__(*args, **kwargs)


@pytest.fixture
def mock_entity_exists() -> YieldFixture[MockEntity]:
    yield MockEntity("mock_exists")
    Entity.entities = []
    Entity.error_if_any_exist = False


@pytest.fixture
def mock_entity_does_not_exist() -> YieldFixture[MockEntity]:
    yield MockEntity("mock_does_not_exist", mock_exists=False)
    Entity.entities = []
    Entity.error_if_any_exist = False


@pytest.fixture(scope="session")
def engine() -> Engine:
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}")


#########
# TESTS #
#########


def test_entity_register(mock_entity_exists: MockEntity) -> None:
    assert mock_entity_exists in Entity.entities


def test_entity_register_order(mock_entity_exists: MockEntity) -> None:
    another_mock = MockEntity("another_one", depends_on=[mock_entity_exists])

    assert Entity.entities[0] == mock_entity_exists
    assert Entity.entities[1] == another_mock


def test_entity_no_engine(mock_entity_exists: MockEntity) -> None:
    with pytest.raises(NoEngineError):
        mock_entity_exists.create()
    with pytest.raises(NoEngineError):
        mock_entity_exists.exists()


def test_entity_get_passed_args() -> None:
    kwargs = dict(name="test", mock_exists=True, mock_kwarg_1="foo", mock_kwarg_2="bar")
    new_mock = MockEntity(**kwargs)  # type: ignore
    check_kwargs = new_mock._get_passed_args()
    # remove "name" before check because it isn't a child class argument, so it shouldn't be in the fn output
    kwargs.pop("name")
    assert kwargs == check_kwargs


def test_entity_get_passed_args_inherited() -> None:
    kwargs = dict(name="merp", mock_kwarg_3="derp", mock_kwarg_4="flerp")
    new_mock = ChildMockEntity(**kwargs)
    check_kwargs = new_mock._get_passed_args()
    # remove "name" before check because it isn't a child class argument, so it shouldn't be in the fn output
    kwargs.pop("name")
    assert kwargs == check_kwargs


def test_entity_does_not_exist(mock_entity_does_not_exist: MockEntity, engine: Engine) -> None:
    Entity._engine = engine
    assert not mock_entity_does_not_exist.exists()


def test_entity_create_if_not_exist(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Entity.create_all(engine)
    assert mock_entity_exists.exists()


def test_entity_create_if_not_error_if_exists(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Entity.create_all(engine)
    # should simply no op, nothing to assert really


def test_entity_create_if_error_if_exists(mock_entity_exists: MockEntity, engine: Engine) -> None:
    mock_entity_exists.error_if_exists = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)


def test_entity_create_if_error_if_any_exist(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Entity.error_if_any_exist = True
    with pytest.raises(EntityExistsError):
        Entity.create_all(engine)
