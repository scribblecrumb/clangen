from dataclasses import dataclass


@dataclass(slots=True)
class PermanentCondition:
    name: str
    severity: str
    is_congenital: bool
    moons_until_discovery: int
    mortality: float
    immune_system_effect: float
    side_effect: dict
    progression: dict
    risks: dict

    def __eq__(self, other):
        return other == self.name
