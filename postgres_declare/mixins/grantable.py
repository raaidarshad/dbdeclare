from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import TextClause, text

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.entity import Entity
from postgres_declare.exceptions import EntityExistsError, InvalidPrivilegeError

if TYPE_CHECKING:
    from postgres_declare.entities.role import Role


class Grantable(ABC):
    def __init__(self, name: str, grants: Sequence[GrantTo] | None = None):
        self.name = name
        if grants:
            self.grant(grants=grants)

    def grant(self, grants: Sequence[GrantTo]) -> None:
        for grant in grants:
            for grantee in grant.to:
                invalid_privileges = self._invalid_privileges(privileges=set(grant.privileges))
                if invalid_privileges:
                    formatted_invalid_privileges = ", ".join(invalid_privileges)
                    formatted_valid_privileges = ", ".join(self._allowed_privileges())
                    raise InvalidPrivilegeError(
                        f"Cannot grant the following privileges for database entity of "
                        f"type {self.__class__.__name__}: {formatted_invalid_privileges}. "
                        f"Valid privileges for this entity include: {formatted_valid_privileges}."
                    )
                else:
                    grantee.grants[self] = grantee.grants[self].union(set(grant.privileges))

    @abstractmethod
    def _exists(self) -> bool:
        pass

    def _safe_grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        if not self._exists():
            raise EntityExistsError(
                f"There is no {self.__class__.__name__} with the "
                f"name {self.name}. The {self.__class__.__name__} "
                f"must exist to grant privileges."
            )
        else:
            self._grant(grantee=grantee, privileges=privileges)

    @abstractmethod
    def _grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        pass

    def _safe_revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        if not self._exists():
            raise EntityExistsError(
                f"There is no {self.__class__.__name__} with the "
                f"name {self.name}. The {self.__class__.__name__} "
                f"must exist to revoke privileges."
            )
        else:
            self._revoke(grantee=grantee, privileges=privileges)

    @abstractmethod
    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        pass

    def _grant_statements(self, grantee: Role, privileges: set[Privilege]) -> Sequence[TextClause]:
        return [
            text(
                f"GRANT {self._format_privileges(privileges)} ON {self.__class__.__name__} {self.name} TO {grantee.name}"
            )
        ]

    def _revoke_statements(self, grantee: Role, privileges: set[Privilege]) -> Sequence[TextClause]:
        return [
            text(
                f"REVOKE {self._format_privileges(privileges)} ON {self.__class__.__name__} {self.name} FROM {grantee.name}"
            )
        ]

    @staticmethod
    @abstractmethod
    def _allowed_privileges() -> set[Privilege]:
        pass

    def _invalid_privileges(self, privileges: set[Privilege]) -> set[Privilege]:
        return privileges.difference(self._allowed_privileges())

    @staticmethod
    def _format_privileges(privileges: set[Privilege]) -> str:
        return ", ".join(privileges)

    @staticmethod
    def _fix_entity_order(grants: Sequence[GrantTo], target_entity: Entity) -> None:
        target_index = target_entity.entities.index(target_entity)
        for grant in grants:
            for grantee in grant.to:
                grantee_index = target_entity.entities.index(grantee)
                if grantee_index > target_index:
                    target_entity.entities.insert(target_index, target_entity.entities.pop(grantee_index))


class GrantableEntity(Grantable, Entity):
    def grant(self, grants: Sequence[GrantTo]) -> None:
        super().grant(grants=grants)
        self._fix_entity_order(grants=grants, target_entity=self)
