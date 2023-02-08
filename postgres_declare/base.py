from sqlalchemy import Engine

from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role


class Base:
    @classmethod
    def create_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in Entity.entities:
            entity._safe_create()

    @classmethod
    def grant_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in Entity.entities:
            if isinstance(entity, Role):
                entity._safe_grant()

    @classmethod
    def run_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        cls.create_all()
        cls.grant_all()

    @classmethod
    def drop_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            entity._safe_drop()

    @classmethod
    def revoke_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            if isinstance(entity, Role):
                entity._safe_revoke()

    @classmethod
    def remove_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        cls.revoke_all()
        cls.drop_all()

    @classmethod
    def _all_entities_exist(cls, engine: Engine | None = None) -> bool:
        if engine:
            Entity._engine = engine
        return all([entity._exists() for entity in Entity.entities])

    @classmethod
    def _all_grants_exist(cls, engine: Engine | None = None) -> bool:
        if engine:
            Entity._engine = engine
        return all([role._grants_exist() for role in Entity.entities if isinstance(role, Role)])

    @classmethod
    def _all_exist(cls, engine: Engine | None = None) -> bool:
        if engine:
            Entity._engine = engine
        return cls._all_entities_exist() and cls._all_grants_exist()
