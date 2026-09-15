# pylint: disable=line-too-long
"""

TODO: Docs


"""
import itertools
from enum import auto, Enum
from random import random, choice
from typing import Optional

import i18n

from scripts.cat.conditions.permanent_condition import PermanentCondition
from scripts.cat.conditions.temporary_condition import TemporaryCondition
from scripts.cat.constants import TEMPORARY_CONDITIONS, PERMANENT_CONDITIONS
from scripts.cat.enums import CatRank
from scripts.cat.pelts import Pelt

from scripts.cat.skills import SkillPath
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank
from scripts.config import get_config
from scripts.game_structure import game


def amount_clanmembers_covered(all_cats, amount_per_med) -> int:
    """
    number of clan members the meds can treat
    """

    medicine_cats = [
        i
        for i in all_cats
        if i.status.alive_in_player_clan
        and i.can_work()
        and i.status.rank.is_any_medicine_rank()
    ]
    full_med = [i for i in medicine_cats if i.status.rank == CatRank.MEDICINE_CAT]
    apprentices = [
        i for i in medicine_cats if i.status.rank == CatRank.MEDICINE_APPRENTICE
    ]

    total_exp = 0
    for cat in medicine_cats:
        total_exp += cat.experience
    total_exp = total_exp * 0.003

    # Determine the total med number. Med cats with certain skill counts
    # as "more" of a med cat.  Only full medicine cat can have their skills have effect
    total_med_number = len(apprentices) / 2
    for cat in full_med:
        if cat.skills.meets_skill_requirement(SkillPath.HEALER, 3):
            total_med_number += 2
        elif cat.skills.meets_skill_requirement(SkillPath.HEALER, 2):
            total_med_number += 1.75
        elif cat.skills.meets_skill_requirement(SkillPath.HEALER, 1):
            total_med_number += 1.5
        else:
            total_med_number += 1

    adjust_med_number = total_med_number + total_exp

    return int(
        adjust_med_number * (amount_per_med + 1)
    )  # number of cats they can care for


def medicine_cats_can_cover_clan(all_cats, amount_per_med) -> bool:
    """
    whether the player has enough meds for the whole clan
    """
    relevant_cats = [c for c in all_cats if c.status.alive_in_player_clan]
    return amount_clanmembers_covered(all_cats, amount_per_med) >= len(relevant_cats)


def get_amount_cat_for_one_medic(clan):
    """Returns the amount of cats one medicine cat can treat"""
    amount = 10
    if clan and clan.game_mode == "classic":
        # just hope nobody has clans with more than 1,000,000 cats in classic
        amount = 1000000
    return amount


def condition_convert(condition_info: dict) -> dict:
    """
    Needs to happen during cat object creation. `version_convert()` happens afterward, so this func is necessary to preempt it.
    """
    new_info = {}

    for condition_type, conditions in condition_info.items():
        if condition_type == "permanent conditions":
            new_perm_info = {}
            for name, con in conditions.items():
                name = name.replace(" ", "_").replace("-", "_")
                new_perm_info[name] = {
                    "severity": con["severity"],
                    "is_congenital": con["born_with"],
                    "moons_until_discovery": con["moons_until"],
                    "moon_gained": con["moon_start"]
                    if "moon_start" in con
                    else con.get("moons_with"),
                    "mortality": round(1 / con["mortality"], 2)
                    if con["mortality"]
                    else 0.0,
                    "immune_system_effect": round(
                        1 / con["illness_infectiousness"][0]["chance"], 2
                    )
                    if con["illness_infectiousness"]
                    else 0.0,
                    "progression": PERMANENT_CONDITIONS[name]["progression"],
                    "risks": {},
                    "current_complication": con["complication"],
                    "omit_moonskip": con["event_triggered"],
                }
                for risk in con["risks"]:
                    risk_name = risk["name"].replace(" ", "_").replace("-", "_")
                    if risk_name in new_perm_info[name]["progression"]:
                        continue
                    new_perm_info[name]["risks"].update(
                        {risk_name: round(1 / risk["chance"], 2)}
                    )
            new_info["permanent_conditions"] = new_perm_info
        if condition_type in ("illnesses", "injuries"):
            new_temp_info = {}
            for name, con in conditions.items():
                name = name.replace(" ", "_").replace("-", "_")
                new_temp_info[name] = {
                    "severity": con["severity"],
                    "duration": con["duration"],
                    "moon_gained": con["moon_start"]
                    if "moon_start" in con
                    else con.get("moons_with"),
                    "mortality": round(1 / con["mortality"], 2)
                    if con["mortality"]
                    else 0.0,
                    "immune_system_effect": round(
                        1 / con["illness_infectiousness"][0].get("lower_by", 5), 2
                    )
                    if con["illness_infectiousness"]
                    else 0.0,
                    "progression": TEMPORARY_CONDITIONS[name]["progression"],
                    "risks": {},
                    "current_complication": con["complication"],
                    "omit_moonskip": con["event_triggered"],
                    "scar_pool_override": con["potential_scars"],
                }
                for risk in con["risks"]:
                    risk_name = risk["name"].replace(" ", "_").replace("-", "_")
                    if risk_name in new_temp_info[name]["progression"]:
                        continue
                    new_temp_info[name]["risks"].update(
                        {risk_name: round(1 / risk["chance"], 2)}
                    )
            new_info["temporary_conditions"] = new_temp_info

    return new_info


def gain_temporary_condition(
    cat,
    name: str,
    omit_moonskip: bool = False,
    prevent_death: bool = False,
    severity: Optional[str] = None,
    scar_pool_override: Optional[list[str]] = None,
):
    """
    Add a temp condition to the cat
    """
    if cat.dead:
        return
    # TODO: check if name is legit condition name
    if name in cat.temporary_conditions:
        return
    if name == "kittencough" and cat.status.rank not in (
        CatRank.KITTEN,
        CatRank.NEWBORN,
    ):
        return

    condition_info = TEMPORARY_CONDITIONS[name]

    cat.temporary_conditions.append(
        TemporaryCondition(
            name=name,
            severity=severity if severity else condition_info["severity"],
            duration=condition_info["duration"],
            mortality=condition_info["mortality"][cat.age]
            if not prevent_death
            else 0.0,
            moon_gained=game.clan.age if game.clan else 0,
            infectiousness=condition_info["infectiousness"],
            immune_system_effect=condition_info["immune_system_effect"],
            progression=condition_info["progression"],
            risks=condition_info["risks"],
            current_complication=None,
            scar_pool_override=scar_pool_override,
            omit_moonskip=omit_moonskip,
        )
    )

    _handle_condition_side_effect(cat, side_effects=condition_info["side_effects"])


def _handle_condition_side_effect(cat, side_effects: dict[str, float]):
    """
    Attempts to give side effect conditions to the cat.
    """
    for effect, chance in side_effects.items():
        avoided = False
        if random() < chance:
            # if this is blood loss, and we have meddies, then they'll try to stop the bleeding
            if effect == "blood_loss" and find_alive_cats_with_rank(
                cat, [CatRank.MEDICINE_CAT], working=True
            ):
                # find what herbs we need
                needed_herbs = itertools.chain.from_iterable(
                    TEMPORARY_CONDITIONS["blood_loss"]["treatment_strength"].values()
                )
                for herb in needed_herbs:
                    if herb in game.clan.herb_supply.entire_supply:
                        # we have an available herb, so we use it and move on to the next side effect
                        avoided = True
                        game.clan.herb_supply.remove_herb(herb, -1)
                        text = i18n.t("screens.med_den.blood_loss", name=cat.name)
                        game.herb_events_list.append(text)
                        break

            if avoided:
                continue

            gain_temporary_condition(cat, effect)


def gain_permanent_condition(
    cat, name: str, is_congenital: bool = False, omit_moonskip: bool = False
):
    if cat.dead:
        return
    if name not in PERMANENT_CONDITIONS:
        print(
            cat.name,
            f"WARNING: {name} is not in the permanent conditions collection.",
        )
        return

    condition = PERMANENT_CONDITIONS[name]

    if any([con in cat.permanent_conditions for con in condition["progression"]]):
        # if cat already has one of the progressions of the new condition, then we shouldn't give it to them
        print(
            f"INFO: {name} was not given to {str(cat.name)} as the cat already had one of the progressions of {name}."
        )
        return

    if is_congenital != condition["can_be_congenital"]:
        print(
            f"WARNING: attempted to give {name} as a congenital condition, but {name} is not allowed to be set as congenital."
        )
        return
    if not is_congenital and not condition["can_be_acquired"]:
        print(
            f"WARNING: attempted to give {name} as an acquired condition, but {name} is not allowed to be set as acquired."
        )
        return

    cat.permanent_conditions.append(
        PermanentCondition(
            name=name,
            severity=condition["severity"],
            is_congenital=is_congenital,
            moons_until_discovery=condition["moons_until_discovery"]
            if is_congenital and cat.status.rank.is_baby()
            else -2,
            moon_gained=game.clan.age if game.clan else 0,
            mortality=condition["mortality"],
            immune_system_effect=condition["immune_system_effect"],
            progression=condition["progression"],
            risks=condition["risks"],
            omit_moonskip=omit_moonskip,
            current_complication=None,
        )
    )

    # APPEARANCE
    if name == "paralyzed":
        cat.pelt.paralyzed = True
    if name == "born without a leg":
        cat.pelt.scars = (*cat.pelt.scars, "NOPAW")
    elif name == "born without a tail":
        cat.pelt.scars = (*cat.pelt.scars, "NOTAIL")
    # remove accessories if need be
    if "NOTAIL" in cat.pelt.scars or "HALFTAIL" in cat.pelt.scars:
        cat.pelt.accessory = tuple(
            acc for acc in cat.pelt.accessory if acc not in Pelt.tail_accessories
        )


def add_congenital_condition(cat):
    possible_conditions = []

    for condition in PERMANENT_CONDITIONS:
        possible = PERMANENT_CONDITIONS[condition]
        if possible["congenital"] in ("always", "sometimes"):
            possible_conditions.append(condition)

    new_condition = choice(possible_conditions)

    if new_condition == "born without a leg":
        cat.pelt.scars = (*cat.pelt.scars, "NOPAW")
    elif new_condition == "born without a tail":
        cat.pelt.scars = (*cat.pelt.scars, "NOTAIL")

    gain_permanent_condition(cat, new_condition, is_congenital=True)


def moon_skip_permanent_condition(cat, condition: PermanentCondition):
    if condition.omit_moonskip:
        return ConditionState.SKIP

    # handling congenital countdown
    if condition.is_congenital:
        if condition.moons_until_discovery >= 0:
            condition.moons_until_discovery -= 1

            if condition.moons_until_discovery == -1:
                condition.moon_gained = game.clan.age
                return ConditionState.REVEAL
            else:
                return ConditionState.SKIP

    mortality = _progress_mortality(cat, condition)
    if mortality == ConditionState.FATAL:
        return ConditionState.FATAL

    return ConditionState.CONTINUE


def moon_skip_temporary_condition(cat, condition: TemporaryCondition):
    if condition.omit_moonskip:
        return ConditionState.SKIP

    mortality = _progress_mortality(cat, condition)
    if mortality == ConditionState.FATAL:
        return ConditionState.FATAL

    recovery_buff = get_config("focus.rest_and_recover.moons_earlier_healed")

    condition.duration -= 1 + recovery_buff

    if condition.duration <= 0:
        if condition.current_complication:
            condition.duration = 1
            return ConditionState.CONTINUE
        else:
            return ConditionState.HEALED
    else:
        return ConditionState.CONTINUE

def _progress_mortality(cat, condition):
    if condition.mortality and random() <= condition.mortality:
        if cat.status.is_leader:
            game.clan.leader_lives -= 1
        cat.die()
        return ConditionState.FATAL

    return ConditionState.CONTINUE

class ConditionState(Enum):
    REVEAL = auto()
    SKIP = auto()
    CONTINUE = auto()
    FATAL = auto()
    HEALED = auto()
