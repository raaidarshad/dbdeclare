from dataclasses import dataclass
from typing import Sequence

from dbdeclare.data_structures.privileges import Privilege
from dbdeclare.mixins.grantable import Grantable


@dataclass
class GrantOn:
    """
    Represents a Sequence of :class:`dbdeclare.data_structures.Privilege` to grant on this
    :class:`dbdeclare.entities.Role` for a Sequence of :class:`dbdeclare.mixins.Grantable`.
    """

    privileges: Sequence[Privilege]
    on: Sequence[Grantable]


# type to represent how to store grants in Role
GrantStore = dict[Grantable, set[Privilege]]
