from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from dbdeclare.data_structures.privileges import Privilege

if TYPE_CHECKING:
    from dbdeclare.entities.role import Role


@dataclass
class GrantTo:
    """
    Represents a Sequence of :class:`dbdeclare.data_structures.Privilege` to grant to a
    :class:`dbdeclare.entities.Role` for a given :class:`dbdeclare.mixins.Grantable`.
    """

    privileges: Sequence[Privilege]
    to: Sequence[Role]
