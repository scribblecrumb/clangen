# pylint: disable=line-too-long
"""

TODO: Docs


"""
from scripts.cat.constants import TEMPORARY_CONDITIONS, PERMANENT_CONDITIONS
from scripts.cat.enums import CatRank

# pylint: enable=line-too-long

from scripts.cat.skills import SkillPath


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
