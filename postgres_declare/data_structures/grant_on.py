from dataclasses import dataclass
from typing import Sequence

from postgres_declare.data_structures.privileges import Privilege
from postgres_declare.entities.grant import GrantableEntity


@dataclass
class GrantOn:
    privileges: Sequence[Privilege]
    on: Sequence[GrantableEntity]


GrantStore = dict[GrantableEntity, set[Privilege]]
