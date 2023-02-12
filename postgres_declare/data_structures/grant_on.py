from dataclasses import dataclass
from typing import Sequence

from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.mixins.grantable import Grantable


@dataclass
class GrantOn:
    """
    Represents a Sequence of :class:`postgres_declare.data_structures.Privilege` to grant to a
    :class:`postgres_declare.entities.Role` on a Sequence of :class:`postgres_declare.mixins.Grantable`.
    """

    privileges: Sequence[Privilege]
    on: Sequence[Grantable]


# type to represent how to store grants in Role
GrantStore = dict[Grantable, set[Privilege]]
