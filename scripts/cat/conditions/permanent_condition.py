from dataclasses import dataclass
from typing import Optional

from scripts.clan_resources.herb.herb_effects import HerbEffect
from scripts.config import get_config


@dataclass(slots=True)
class PermanentCondition:
    name: str
    severity: str
    is_congenital: bool
    removed_on_death: bool
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

    def __repr__(self):
        return self.name

    def apply_lack_of_herb(self, effect: HerbEffect):
        if effect == HerbEffect.RISK:
            for risk in self.risks:
                self.risks[risk] += get_config("clan_resources.herbs.base_risk_effect")

        elif effect == HerbEffect.PROGRESSION:
            for progression in self.progression:
                self.progression[progression]["chance"] += get_config(
                    "clan_resources.herbs.base_progression_effect"
                )

        elif effect == HerbEffect.MORTALITY:
            if self.mortality:
                self.mortality += get_config(
                    "clan_resources.herbs.base_mortality_effect"
                )

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
