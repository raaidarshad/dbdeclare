from typing import Sequence

from postgres_declare.data_structures.grant_to import GrantTo
from postgres_declare.entities.entity import Entity


class GrantableEntity(Entity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        grants: Sequence[GrantTo] | None = None,
    ):
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)
        if grants:
            self.grant(grants=grants)

    def grant(self, grants: Sequence[GrantTo]) -> None:
        for grant in grants:
            for grantee in grant.to:
                grantee.grants[self] = grantee.grants[self].union(set(grant.privileges))
        # ensure entity order is correct
        this_index = self.entities.index(self)
        for grant in grants:
            for grantee in grant.to:
                grantee_index = self.entities.index(grantee)
                if grantee_index > this_index:
                    self.entities.insert(this_index, self.entities.pop(grantee_index))
