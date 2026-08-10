from dataclasses import dataclass


@dataclass(slots=True)
class TemporaryCondition:
    name: str
    severity: str
    duration: int
    mortality: float
    infectiousness: float
    immune_system_effect: float
    progression: dict
    risks: dict

    omit_moonskip: bool = False

    def __eq__(self, other):
        return other == self.name
