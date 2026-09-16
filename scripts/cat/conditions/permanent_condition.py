from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class PermanentCondition:
    name: str
    severity: str
    is_congenital: bool
    moons_until_discovery: int
    moon_gained: int
    mortality: float
    immune_system_effect: float
    progression: dict
    risks: dict
    current_complication: Optional[str]

    requires_scar: bool = False
    omit_moonskip: bool = False

    possible_scars: list = field(default_factory=list)

    def __eq__(self, other):
        return other == self.name
