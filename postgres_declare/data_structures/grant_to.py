from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from postgres_declare.data_structures.privileges import Privilege

if TYPE_CHECKING:
    from postgres_declare.entities.role import Role


@dataclass
class GrantTo:
    privileges: Sequence[Privilege]
    to: Sequence[Role]
