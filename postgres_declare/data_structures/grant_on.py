from dataclasses import dataclass
from typing import Sequence

from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.grantable import Grantable


@dataclass
class GrantOn:
    privileges: Sequence[Privilege]
    on: Sequence[Grantable]


GrantStore = dict[Grantable, set[Privilege]]
