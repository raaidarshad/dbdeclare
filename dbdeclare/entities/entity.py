from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Sequence

from sqlalchemy import Engine

from dbdeclare.exceptions import EntityExistsError, NoEngineError


class Entity(ABC):
    """
    Base class to inherit from for all entities. Defines methods common to all entities, abstract methods that are
    needed for all entities, and class methods that enable collection of entities for easy cluster interaction.
    """

    entities: list["Entity"] = []
    check_if_any_exist: bool = False
    _engine: Engine | None = None

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        check_if_exists: bool | None = None,
    ):
        """
        :param name: Unique name of the entity. Cluster-level entities must be unique, database-level entities must be unique within a database.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        """
        # TODO have "name" be a str class that validates via regex for valid postgres names
        self.name = name

        # explicit None check because False requires different behavior
        if check_if_exists is None:
            self.check_if_exists = self.__class__.check_if_any_exist
        else:
            self.check_if_exists = check_if_exists

        if not depends_on:
            depends_on = []
        self.depends_on: Sequence["Entity"] = depends_on

        self.__class__._register(self)

    def __hash__(self) -> int:
        return hash((self.name, self.__class__.__name__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.name, self.__class__.__name__) == (other.name, other.__class__.__name__)

    @classmethod
    def _register(cls, entity: "Entity") -> None:
        """
        Appends an entity to the running list of all entities.
        :param entity: Any given entity, can be thought of as operating on a subclassed `self`.
        """
        # TODO add code to make sure there are no duplicate entities
        cls.entities.append(entity)

    @classmethod
    def engine(cls) -> Engine:
        """
        Convenience wrapper to safely get the main engine.
        :return: A :class:`sqlalchemy.Engine` if one has been assigned, otherwise raises an exception.
        """
        if cls._engine:
            return cls._engine
        else:
            raise NoEngineError("There is no SQLAlchemy Engine present. `Base._engine` must have " "a valid engine.")

    @abstractmethod
    def _create(self) -> None:
        """
        Create this entity in the cluster.
        """
        pass

    def _safe_create(self) -> None:
        """
        Run an existence check before attempting to create the entity in the cluster.
        """
        if not self._exists():
            self._create()
        else:
            if self.check_if_exists or self.check_if_any_exist:
                raise EntityExistsError(
                    f"There is already a {self.__class__.__name__} with the "
                    f"name {self.name}. If you want to proceed anyway, set "
                    f"the `check_if_exists` parameter to False. This will "
                    f"simply skip over the existing entity."
                )
            else:
                # TODO log that we no-op?
                pass

    @abstractmethod
    def _exists(self) -> bool:
        """
        Check if this entity currently exists in the cluster.
        :return: True if it exists, False if it does not.
        """
        pass

    @abstractmethod
    def _drop(self) -> None:
        """
        Drop this entity from the cluster.
        """
        pass

    def _safe_drop(self) -> None:
        """
        Run an existence check before attempting to drop the entity from the cluster.
        """
        if self._exists():
            self._drop()
        else:
            if self.check_if_exists or self.check_if_any_exist:
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name} to remove. If you want to proceed "
                    f"anyway, set the `check_if_exists` parameter to False. "
                    f"This will simply skip over the removal of this "
                    f"entity that does not exist in the cluster."
                )
            else:
                # TODO log that we no-op?
                pass

    def _get_passed_args(self) -> dict[str, Any]:
        """
        Helper to grab all the arguments to __init__ that aren't in the superclass and have a non-None value. Useful
        for subclasses.
        :return: A dict mapping the names of init arguments to their values.
        """
        return {
            k: v
            for k, v in vars(self).items()
            if (k not in signature(self.__class__.__bases__[0].__init__).parameters)  # type: ignore
            and (v is not None)
            and (k != "_grant_name")
        }
