from sqlalchemy import Engine

from postgres_declare.entities.entity import Entity


class Base:
    @classmethod
    def create_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in Entity.entities:
            entity._safe_create()

    @classmethod
    def remove_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            entity._safe_remove()
