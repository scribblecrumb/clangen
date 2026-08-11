from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class TemporaryCondition:
    name: str
    severity: str
    duration: int
    mortality: float
    moon_gained: int
    infectiousness: float
    immune_system_effect: float
    progression: dict
    risks: dict
    current_complication: Optional[str]
    scar_pool_override: list[str]

    omit_moonskip: bool = False

    def __eq__(self, other):
        return other == self.name
