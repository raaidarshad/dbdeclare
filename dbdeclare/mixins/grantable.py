from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import TextClause, text

from dbdeclare.data_structures.grant_to import GrantTo
from dbdeclare.data_structures.privileges import Privilege
from dbdeclare.entities.entity import Entity
from dbdeclare.exceptions import EntityExistsError, InvalidPrivilegeError

if TYPE_CHECKING:
    from dbdeclare.entities.role import Role


class Grantable(ABC):
    """
    Mixin for entities that can have privileges granted or revoked.
    """

    def __init__(self, name: str, grants: Sequence[GrantTo] | None = None):
        """
        :param name: Unique name of the grantable.
        :param grants: Sequence of grant definitions in the form of :class:`dbdeclare.data_structures.GrantTo`.
        """
        self.name = name
        self._grant_name = name
        if grants:
            self.grant(grants=grants)

    def grant(self, grants: Sequence[GrantTo]) -> None:
        """
        Parses the provided grants, checks their validity, and stores them in the appropriate :class:`dbdeclare.entities.Role`.
        :param grants: Sequence of grant definitions in the form of :class:`dbdeclare.data_structures.GrantTo`.
        """
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
        """
        Check if this entity currently exists in the cluster.
        """
        pass

    def _safe_grant(self, grantee: Role, privileges: set[Privilege]) -> None:
        """
        Run an existence check before attempting to grant privileges.
        :param grantee: The :class:`dbdeclare.entities.Role` to grant privileges to.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to grant.
        """
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
        """
        Grant privileges on this entity to the grantee.
        :param grantee: The :class:`dbdeclare.entities.Role` to grant privileges to.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to grant.
        """
        pass

    def _safe_revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        """
        Run an existence check before attempting to revoke privileges.
        :param grantee: The :class:`dbdeclare.entities.Role` to revoke privileges from.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to revoke.
        """
        if not self._exists():
            raise EntityExistsError(
                f"There is no {self.__class__.__name__} with the "
                f"name {self.name}. The {self.__class__.__name__} "
                f"must exist to revoke privileges."
            )
        else:
            self._revoke(grantee=grantee, privileges=privileges)

    @abstractmethod
    def _grants_exist(self, grantee: Role, privileges: set[Privilege]) -> bool:
        """
        Check if these privileges are granted to the grantee.
        :param grantee: The :class:`dbdeclare.entities.Role` to check access for.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to check on.
        """
        pass

    @abstractmethod
    def _revoke(self, grantee: Role, privileges: set[Privilege]) -> None:
        """
        Revoke privileges on this entity from the grantee.
        :param grantee: The :class:`dbdeclare.entities.Role` to revoke privileges from.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to revoke.
        """
        pass

    def _grant_statements(self, grantee: Role, privileges: set[Privilege]) -> Sequence[TextClause]:
        """
        Generates a grant statement to commit via SQL.
        :param grantee: The :class:`dbdeclare.entities.Role` to grant privileges to.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to grant.
        :return: A Sequence of :class:`sqlalchemy.TextClause` that represent the desired grant statements.
        """
        return [
            text(
                f"GRANT {self._format_privileges(privileges)} ON {self.__class__.__name__} {self._grant_name} TO {grantee.name}"
            )
        ]

    def _revoke_statements(self, grantee: Role, privileges: set[Privilege]) -> Sequence[TextClause]:
        """
        Generates a revoke statement to commit via SQL.
        :param grantee: The :class:`dbdeclare.entities.Role` to revoke privileges from.
        :param privileges: The set of :class:`dbdeclare.data_structures.Privilege` to revoke.
        :return: A Sequence of :class:`sqlalchemy.TextClause` that represent the desired revoke statements.
        """
        return [
            text(
                f"REVOKE {self._format_privileges(privileges)} ON {self.__class__.__name__} {self._grant_name} FROM {grantee.name}"
            )
        ]

    @staticmethod
    @abstractmethod
    def _allowed_privileges() -> set[Privilege]:
        """
        Define the set of :class:`dbdeclare.data_structures.Privilege` that are allowed for this entity.
        :return: The set of :class:`dbdeclare.data_structures.Privilege` that are allowed for this entity.
        """
        pass

    def _check_privileges(self, declared_privileges: set[Privilege], existing_privileges: set[Privilege]) -> bool:
        """
        Check the in-code declared privileges against the in-cluster existing privileges.
        :param declared_privileges: A set of :class:`dbdeclare.data_structures.Privilege` declared in code for this entity.
        :param existing_privileges: A set of :class:`dbdeclare.data_structures.Privilege` declared in cluster for this entity.
        :return: True if the declared privileges are a subset of the existing privileges. Accounts for ALL_PRIVILEGES.
        """
        if Privilege.ALL_PRIVILEGES in declared_privileges:
            declared = self._allowed_privileges()
            declared.discard(Privilege.ALL_PRIVILEGES)
        else:
            declared = declared_privileges

        return declared.issubset(existing_privileges)

    def _invalid_privileges(self, privileges: set[Privilege]) -> set[Privilege]:
        """
        Find all invalid privileges for this entity type.
        :param privileges: A set of :class:`dbdeclare.data_structures.Privilege` to check for invalid entries.
        :return: A set of :class:`dbdeclare.data_structures.Privilege` that are invalid. Empty if all valid.
        """
        return privileges.difference(self._allowed_privileges())

    @staticmethod
    def _format_privileges(privileges: set[Privilege]) -> str:
        """
        Helper method that formats privileges for a SQL statement.
        :param privileges: A set of :class:`dbdeclare.data_structures.Privilege` to format.
        :return: A comma-separated list of the provided privileges as a string.
        """
        return ", ".join(privileges)

    @staticmethod
    def _fix_entity_order(grants: Sequence[GrantTo], target_entity: Entity) -> None:
        """
        If a grant relationship exists between a Grantable and a Role, the Role must exist prior to the Grantable.
        This method can be used by subclasses to ensure the entity order is correct, likely in the grant method.
        :param grants: A Sequence of :class:`dbdeclare.data_structures.GrantTo`.
        :param target_entity: The target to check against. Likely `self` or similar.
        """
        target_index = target_entity.entities.index(target_entity)
        for grant in grants:
            for grantee in grant.to:
                grantee_index = target_entity.entities.index(grantee)
                if grantee_index > target_index:
                    target_entity.entities.insert(target_index, target_entity.entities.pop(grantee_index))

    def _extract_privileges(self, acl: str, grantee: Role) -> set[Privilege]:
        """
        Extracts a set of :class:`dbdeclare.data_structures.Privilege` from a Postgres ACL statement.
        The expected format is: grantee=xxxx/grantor, where grantee and grantor are roles and the "x"s indicate
        potential privilege codes. If the grantee is absent, the grantee is PUBLIC.
        :param acl: Raw acl string from Postgres in the form of grantee=xxxx/grantor.
        :param grantee: The :class:`dbdeclare.entities.Role` to filter to.
        :return: A set of :class:`dbdeclare.data_structures.Privilege` that exist in cluster, granted to the grantee.
        """
        m = re.match(r"(\w*)=(\w*)\/(\w*)", acl)
        if m:
            if m.group(1) == grantee.name:
                raw_privileges = m.group(2)
                return {self._code_to_privilege(code) for code in raw_privileges}
        return set()

    @staticmethod
    def _code_to_privilege(code: str) -> Privilege:
        """
        Wrapper around a dictionary to map from a letter code to a typed privilege.
        :param code: A letter code representing a privilege. See `Postgres docs <https://www.postgresql.org/docs/current/ddl-priv.html#PRIVILEGE-ABBREVS-TABLE>`_ for more.
        :return: A :class:`dbdeclare.data_structures.Privilege` corresponding to the provided letter code.
        """
        return {
            "r": Privilege.SELECT,
            "w": Privilege.UPDATE,
            "a": Privilege.INSERT,
            "d": Privilege.DELETE,
            "D": Privilege.TRUNCATE,
            "x": Privilege.REFERENCES,
            "t": Privilege.TRIGGER,
            "X": Privilege.EXECUTE,
            "U": Privilege.USAGE,
            "C": Privilege.CREATE,
            "c": Privilege.CONNECT,
            "T": Privilege.TEMPORARY,
        }[code]


class GrantableEntity(Grantable, Entity):
    """
    Convenience class that inherits from Grantable and Entity.
    """

    def grant(self, grants: Sequence[GrantTo]) -> None:
        super().grant(grants=grants)
        self._fix_entity_order(grants=grants, target_entity=self)
