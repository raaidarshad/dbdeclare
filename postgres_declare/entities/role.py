from collections import defaultdict
from datetime import datetime
from typing import Sequence

from sqlalchemy import TextClause, text

from postgres_declare.data_structures.grant_on import GrantOn, GrantStore
from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.cluster_entity import ClusterEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.exceptions import EntityExistsError


class Role(ClusterEntity):
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
        for grant in grants:
            for grantor in grant.on:
                self.grants[grantor].union(set(grant.privileges))

    def _safe_grant(self) -> None:
        if self.grants:
            grantors = {grantor for grantor in self.grants.keys() if grantor._exists()}
            grantors_that_do_not_exist = set(self.grants.keys()).difference(grantors)
            # if the role doesn't exist, say so
            if not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name}. The {self.__class__.__name__} "
                    f"must exist to grant privileges."
                )
            # if the grantors don't exist, say so, and say which ones
            elif grantors_that_do_not_exist:
                missing_grantors = ", ".join(
                    [f"{g.__class__.__name__.upper()} - {g.name}" for g in grantors_that_do_not_exist]
                )
                raise EntityExistsError(
                    f"There are no entities of the following kind and name: "
                    f"{missing_grantors}. "
                    f"These must exist to grant privileges."
                )
            # if everything needed exists, run _grant
            else:
                self._grant()

    def _grant(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._grant_statements())

    def _grant_statements(self) -> Sequence[TextClause]:
        return [
            text(
                f"GRANT {self._format_privileges(privileges)} ON {grantor.__class__.__name__.upper()} {grantor.name} TO {self.name}"
            )
            for grantor, privileges in self.grants.items()
        ]

    def _safe_revoke(self) -> None:
        if self.grants:
            grantors = {grantor for grantor in self.grants.keys() if grantor._exists()}
            grantors_that_do_not_exist = set(self.grants.keys()).difference(grantors)
            # if the role doesn't exist, say so
            if not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name}. The {self.__class__.__name__} "
                    f"must exist to revoke privileges."
                )
            # if the grantors don't exist, say so, and say which ones
            elif grantors_that_do_not_exist:
                missing_grantors = ", ".join(
                    [f"{g.__class__.__name__.upper()} - {g.name}" for g in grantors_that_do_not_exist]
                )
                raise EntityExistsError(
                    f"There are no entities of the following kind and name: "
                    f"{missing_grantors}. "
                    f"These must exist to revoke privileges."
                )
            # if everything needed exists, run _grant
            else:
                self._revoke()

    def _revoke(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._revoke_statements())

    def _revoke_statements(self) -> Sequence[TextClause]:
        return [
            text(
                f"REVOKE {self._format_privileges(privileges)} ON {grantor.__class__.__name__.upper()} {grantor.name} FROM {self.name}"
            )
            for grantor, privileges in self.grants.items()
        ]

    @staticmethod
    def _format_privileges(privileges: set[Privilege]) -> str:
        return ", ".join(privileges)
