from sqlalchemy import Engine

from postgres_declare.entities.entity import Entity
from postgres_declare.grant import Grantable


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
            if isinstance(entity, Grantable):
                entity._grant()

    @classmethod
    def run_all(cls, engine: Engine) -> None:
        Entity._engine = engine
        cls.create_all()
        cls.grant_all()

    @classmethod
    def remove_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            entity._safe_remove()
