from dataclasses import dataclass


@dataclass(slots=True)
class TemporaryCondition:
    name: str
    severity: str
    duration: int
    mortality: float
    infectiousness: float
    immune_system_effect: float
    side_effect: dict
    progression: dict
    risks: dict

    def __eq__(self, other):
        return other == self.name
