from dataclasses import dataclass, field
from typing import Optional

from scripts.clan_resources.herb.herb_effects import HerbEffect
from scripts.config import get_config


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

    is_complication: bool = False
    omit_moonskip: bool = False

    def __eq__(self, other):
        return other == self.name

    def __repr__(self):
        return self.name

    def apply_lack_of_herb(self, effect: HerbEffect):
        if effect == HerbEffect.RISK:
            for risk in self.risks:
                self.risks[risk] += 0.05

        if effect == HerbEffect.PROGRESSION:
            for progression in self.progression:
                self.progression[progression]["chance"] += 0.05

        if effect == HerbEffect.MORTALITY:
            if self.mortality:
                self.mortality += 0.05

    def apply_herb_effect(
        self, effect: HerbEffect, strength: int, amount_modifier: float
    ):
        if effect == HerbEffect.RISK:
            for risk in self.risks:
                self.risks[risk] -= (
                    get_config("clan_resources.herbs.base_risk_effect")
                ) + amount_modifier * strength

        elif effect == HerbEffect.PROGRESSION:
            for progression in self.progression:
                self.progression[progression]["chance"] += (
                    get_config("clan_resources.herbs.base_progression_effect")
                    + amount_modifier * strength
                )

        elif effect == HerbEffect.MORTALITY:
            if self.mortality:
                self.mortality += (
                    get_config("clan_resources.herbs.base_mortality_effect")
                    + amount_modifier * strength
                )

        elif effect == HerbEffect.DURATION:
            amount = get_config("clan_resources.herbs.base_duration_effect")
            if strength == 3:
                amount += 1  # max duration effect is 2
            self.duration -= amount
