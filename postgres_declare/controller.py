from sqlalchemy import Engine

from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role


class Controller:
    """
    Entrypoint for creating/dropping database entities and granting/revoking privileges once they are
    defined in code. This is a wrapper of sorts around :class:`postgres_declare.entities.entity.Entity`.
    """

    @classmethod
    def create_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to create all defined entities. Typically run via `run_all`.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        for entity in Entity.entities:
            entity._safe_create()

    @classmethod
    def grant_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to grant all defined privileges. Requires entities to exist, typically run via `run_all` or after
        `create_all`.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        for entity in Entity.entities:
            if isinstance(entity, Role):
                entity._safe_grant()

    @classmethod
    def run_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to create all defined entities then grant all defined privileges. Main way to do so.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        cls.create_all()
        cls.grant_all()

    @classmethod
    def drop_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to drop all defined entities. Typically run via `remove_all`.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        for entity in reversed(Entity.entities):
            entity._safe_drop()

    @classmethod
    def revoke_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to revoke all defined privileges. Requires entities to exist, typically run via `remove_all` or before
        `drop_all`.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        for entity in reversed(Entity.entities):
            if isinstance(entity, Role):
                entity._safe_revoke()

    @classmethod
    def remove_all(cls, engine: Engine | None = None) -> None:
        """
        Attempts to revoke all defined privileges then drop all defined entities. Main way to do so.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        cls.revoke_all()
        cls.drop_all()

    @classmethod
    def _all_entities_exist(cls, engine: Engine | None = None) -> bool:
        """
        Checks if all defined entities exist in the cluster.
        :param engine:  A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        return all([entity._exists() for entity in Entity.entities])

    @classmethod
    def _all_grants_exist(cls, engine: Engine | None = None) -> bool:
        """
        Checks if all defined grants exist in the cluster.
        :param engine:  A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        return all([role._grants_exist() for role in Entity.entities if isinstance(role, Role)])

    @classmethod
    def _all_exist(cls, engine: Engine | None = None) -> bool:
        """
        Checks if all defined entities and grants exist in the cluster.
        :param engine:  A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        cls._handle_engine(engine)
        return cls._all_entities_exist() and cls._all_grants_exist()

    @staticmethod
    def _handle_engine(engine: Engine | None = None) -> None:
        """
        Utility to assign the engine if it is provided.
        :param engine: A :class:`sqlalchemy.Engine` that defines the connection to a Postgres instance/cluster.
        """
        if engine:
            Entity._engine = engine
