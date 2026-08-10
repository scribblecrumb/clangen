from dataclasses import dataclass


@dataclass(slots=True)
class PermanentCondition:
    severity: str
    moons_until_discovery: int
    mortality: float
    immune_system_effect: float
    side_effect: dict
    progression: dict
    risks: dict
