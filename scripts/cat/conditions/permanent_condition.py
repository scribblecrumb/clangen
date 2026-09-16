from dataclasses import dataclass
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

    omit_moonskip: bool = False

    def __eq__(self, other):
        return other == self.name
