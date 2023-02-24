from collections import defaultdict
from datetime import datetime
from typing import Sequence

from sqlalchemy import TextClause, text

from dbdeclare.data_structures.grant_on import GrantOn, GrantStore
from dbdeclare.entities.cluster_entity import ClusterEntity
from dbdeclare.entities.entity import Entity
from dbdeclare.exceptions import EntityExistsError


class Role(ClusterEntity):
    """
    Represents a Postgres `Role <https://www.postgresql.org/docs/current/database-roles.html>`_.
    """

    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        superuser: bool | None = None,
        createdb: bool | None = None,
        createrole: bool | None = None,
        inherit: bool | None = None,
        login: bool | None = None,
        replication: bool | None = None,
        bypassrls: bool | None = None,
        connection_limit: int | None = None,
        password: str | None = None,
        encrypted: bool | None = None,
        valid_until: datetime | None = None,
        in_role: Sequence["Role"] | None = None,
        role: Sequence["Role"] | None = None,
        admin: Sequence["Role"] | None = None,
        grants: Sequence[GrantOn] | None = None,
    ):
        """
        All __init__ params correspond to CREATE ROLE arguments and options, see
        `official Postgres documentation <https://www.postgresql.org/docs/current/sql-createrole.html>`_.


        :param name: Unique name of the entity. Must be unique across the cluster.
        :param depends_on: Any entities that should be created before this one.
        :param check_if_exists: Flag to set existence check behavior. If `True`, will raise an exception during _safe_create if the entity already exists, and will raise an exception during _safe_drop if the entity does not exist.
        :param superuser: Flag to declare a role as a superuser. Postgres defaults to `False`.
        :param createdb: Flag for the ability to create databases. Postgres defaults to `False`.
        :param createrole: Flag for the ability to manage roles. Postgres defaults to `False`.
        :param inherit: Flag to specify that the role will inherit privileges of roles it is a member of. Postgres defaults to `True`.
        :param login: Flag for the ability to login (aka be a user). Postgres defaults to `False`.
        :param replication: Flag to specify a replication role. Postgres defaults to `False`.
        :param bypassrls: Flag to indicate the role should bypass RLS policies. Postgres defaults to `False`.
        :param connection_limit: Number of concurrent connections the role can make. Postgres defaults to -1, which means no limit.
        :param password: Set the role's password. Postgres defaults to a null password, which means password authentication always fails.
        :param encrypted: Keyword has no effect but is present for backwards compatability. Consider removing.
        :param valid_until: Sets a date and time after which the role's password is no longer valid. Postgres defaults to no limit.
        :param in_role: Sequence of :class:`dbdeclare.entities.Role` that this role belongs to.
        :param role: Sequence of :class:`dbdeclare.entities.Role` that belong to this role.
        :param admin: Like the `role` param above, but gives the roles the right to grant membership to this role to other roles.
        :param grants: Sequence of :class:`dbdeclare.data_structures.GrantOn` to specify privileges this role has in relation to other entities.
        """
        self.superuser = superuser
        self.createdb = createdb
        self.createrole = createrole
        self.inherit = inherit
        self.login = login
        self.replication = replication
        self.bypassrls = bypassrls
        self.connection_limit = connection_limit
        self.password = password
        self.encrypted = encrypted
        self.valid_until = valid_until
        self.in_role = in_role
        self.role = role
        self.admin = admin
        self.grants: GrantStore = defaultdict(set)
        if grants:
            self.grant(grants=grants)
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def _create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE ROLE {self.name}"
        props = self._get_passed_args()

        for k, v in props.items():
            match k, v:
                case "password", str(v):
                    if "encrypted" in props:
                        statement = f"{statement} ENCRYPTED"
                    statement = f"{statement} PASSWORD '{v}'"
                    if "valid_until" in props:
                        timestamp = props.get("valid_until")
                        statement = f"{statement} VALID UNTIL '{timestamp}'"

                case k, bool(v) if k != "encrypted":
                    flag = k.upper()
                    if not v:
                        flag = f"NO{flag}"
                    statement = f"{statement} {flag}"

                case "connection_limit", int(v):
                    statement = f"{statement} CONNECTION LIMIT {v}"

                case "grants", _:
                    # ignore grants argument, it is handled by the _grant command
                    pass

                # match a sequence with at least one element to filter out empty sequence
                case k, [first, *roles]:
                    option = k.upper().replace("_", " ")
                    roles = [first] + roles  # type: ignore
                    formatted_roles = ", ".join([r.name for r in roles])
                    statement = f"{statement} {option} {formatted_roles}"

        # TODO binding isn't working, switching to simple quotes for now
        return [text(statement)]

    def _exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_authid WHERE rolname=:role)").bindparams(role=self.name)

    def _drop_statements(self) -> Sequence[TextClause]:
        return [text(f"DROP ROLE {self.name}")]

    def grant(self, grants: Sequence[GrantOn]) -> None:
        """
        Sets the privileges to grant on this role to the specified entities.
        :param grants: A Sequence of :class:`dbdeclare.data_structures.GrantOn` to store.
        """
        for grant in grants:
            for target in grant.on:
                self.grants[target] = self.grants[target].union(set(grant.privileges))

    def _safe_grant(self) -> None:
        """
        Performs an existence check before executing grant statements in the cluster.
        """
        if self.grants:
            if not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name}. The {self.__class__.__name__} "
                    f"must exist to grant privileges."
                )
            else:
                for target, privileges in self.grants.items():
                    target._safe_grant(grantee=self, privileges=privileges)

    def _grants_exist(self) -> bool:
        """
        Checks to see if all in-code declared grants exist in the cluster.
        """
        if self.grants:
            if not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name}. The {self.__class__.__name__} "
                    f"must exist to alter privileges."
                )
            else:
                return all(
                    [
                        target._grants_exist(grantee=self, privileges=privileges)
                        for target, privileges in self.grants.items()
                    ]
                )
        else:
            # if there aren't any grants, return True because technically all specified grants are present
            return True

    def _safe_revoke(self) -> None:
        """
        Performs an existence check before executing revoke statements in the cluster.
        """
        if self.grants:
            if not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name}. The {self.__class__.__name__} "
                    f"must exist to revoke privileges."
                )
            else:
                for target, privileges in self.grants.items():
                    target._safe_revoke(grantee=self, privileges=privileges)
