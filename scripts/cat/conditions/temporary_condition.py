from dataclasses import dataclass

from scripts.cat.conditions.base_condition_class import BaseCondition
from scripts.clan_resources.herb.herb_effects import HerbEffect
from scripts.config import get_config


@dataclass(slots=True)
class TemporaryCondition(BaseCondition):
    duration: int
    infectiousness: float
    scar_pool_override: list[str]
    is_complication: bool = False

    def __eq__(self, other):
        return other == self.name

    def __repr__(self):
        return self.name

    def apply_herb_effect(
        self, effect: HerbEffect, strength: int, amount_modifier: float
    ):
        super().apply_herb_effect(effect, strength, amount_modifier)

        if effect == HerbEffect.DURATION:
            amount = get_config("clan_resources.herbs.base_duration_effect")
            if strength == 3:
                amount += 1  # max duration effect is 2
            self.duration -= amount
