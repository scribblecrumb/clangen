import logging
from random import choice, random
from typing import Optional

import i18n

from scripts.cat.cats import Cat
from scripts.cat.conditions.conditions import (
    update_temporary_condition_state,
    ConditionState,
    gain_temporary_condition,
    gain_permanent_condition,
    update_permanent_condition_state,
)
from scripts.cat.conditions.temporary_condition import TemporaryCondition
from scripts.cat.constants import TEMPORARY_CONDITIONS, PERMANENT_CONDITIONS
from scripts.cat.enums import CatRank, CatAge
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank
from scripts.clan_package.settings import get_clan_setting
from scripts.config import get_config
from scripts.events_module.consequences import check_stolen_vitality
from scripts.events_module.event_information import EventInformation
from scripts.events_module.text_adjust import event_text_adjust, get_leader_life_notice
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource

logger = logging.getLogger(__name__)


def handle_temporary_conditions(cat: Cat):
    conditions_to_remove = []

    event_list = []
    cat_dict = {"m_c": cat}

    for condition in cat.temporary_conditions.copy():
        if condition.omit_moonskip:
            continue

        state = update_temporary_condition_state(cat, condition)

        if state == ConditionState.SKIPPED:
            continue

        elif state == ConditionState.FATAL:
            try:
                possible_string_list = load_lang_resource(
                    "healed_and_death_strings/injury_death_strings.json"
                )[condition.name]
                event = choice(possible_string_list)

                # first string in the list is always appropriate for history text
                history_text = possible_string_list[0]
            except KeyError:
                logging.warning(
                    "%s does not have an condition death string, placeholder used.",
                    condition.name,
                )

                event = i18n.t("defaults.injury_death_event")
                history_text = i18n.t("defaults.injury_death_history")

            event = event_text_adjust(Cat, event, main_cat=cat)

            # add life loss message
            if cat.status.is_leader:
                event = event + " " + get_leader_life_notice(str(cat.name))
                if extra_text := check_stolen_vitality(cat, 1):
                    event += " " + extra_text

            # add death to history
            cat.history.add_death(condition=condition, death_text=history_text.strip())

            # clear event list first to make sure any heal or risk events from other injuries are not shown
            event_list.clear()
            event_list.append(event)
            game.herb_events_list.append(event)
            break

        elif state == ConditionState.HEALED:
            event = _attempt_scarring(
                cat, condition, possible_scars=condition.possible_scars
            )

            if not event:
                try:
                    event = _get_valid_string_from_list(
                        load_lang_resource(
                            "healed_and_death_strings/injury_healed_strings.json"
                        )[condition.name],
                        cat,
                    )
                except KeyError:
                    logger.warning(
                        "%s couldn't be found in the healed strings dict! placeholder used.",
                        condition,
                    )

                    # try to translate the string
                    new_injury = i18n.t(f"conditions.temporary_conditions.{condition}")
                    new_injury.replace("conditions.temporary_conditions.", "")

                    event = i18n.t("defaults.injury_healed_event", injury=new_injury)

            event = event_text_adjust(Cat, event, main_cat=cat)

            game.herb_events_list.append(event)

            cat.history.remove_possible_history(condition)
            conditions_to_remove.append(condition)

            if condition.is_complication:
                # if it's a complication, take it off whatever condition it's linked to
                for c in cat.temporary_conditions + cat.permanent_conditions:
                    if condition == c.current_complication:
                        c.current_complication = None

            continue

        elif state == ConditionState.CONTINUING:
            conditions_to_remove = _check_risks_and_progressions(
                cat, condition, conditions_to_remove
            )

    for c in conditions_to_remove:
        cat.temporary_conditions.remove(c)

    if len(event_list) > 0:
        event_string = " ".join(event_list)
    else:
        event_string = None

    if event_string:
        types = ["health"]
        if cat.dead:
            types.append("birth_death")
        game.cur_events_list.append(
            EventInformation(event_string, types, cat_dict=cat_dict)
        )


def handle_permanent_conditions(cat: Cat):
    event_list = []
    conditions_to_remove = []
    cat_dict = {"m_c": cat}

    for condition in cat.permanent_conditions.copy():
        if condition.omit_moonskip:
            continue

        state = update_permanent_condition_state(cat, condition)

        if state == ConditionState.SKIPPED:
            continue

        elif state == ConditionState.FATAL:
            try:
                possible_string_list = load_lang_resource(
                    "healed_and_death_strings/permanent_death_strings.json"
                )[condition.name]
                event = choice(possible_string_list)

                # first string in the list is always appropriate for history text
                history_text = possible_string_list[0]
            except KeyError:
                logging.warning(
                    "%s does not have an condition death string, placeholder used.",
                    condition.name,
                )

                event = i18n.t("defaults.injury_death_event")
                history_text = i18n.t("defaults.injury_death_history")

            event = event_text_adjust(Cat, event, main_cat=cat)

            # add life loss message
            if cat.status.is_leader:
                event = event + " " + get_leader_life_notice(str(cat.name))
                if extra_text := check_stolen_vitality(cat, 1):
                    event += " " + extra_text

            # add death to history
            cat.history.add_death(condition=condition, death_text=history_text.strip())

            # clear event list first to make sure any heal or risk events from other injuries are not shown
            event_list.clear()
            event_list.append(event)
            game.herb_events_list.append(event)
            break

        elif state == ConditionState.REVEALED:
            # TODO: get strings
            pass

        elif state == ConditionState.CONTINUING:
            conditions_to_remove = _check_risks_and_progressions(
                cat, condition, conditions_to_remove
            )

    for c in conditions_to_remove:
        cat.temporary_conditions.remove(c)

    if len(event_list) > 0:
        event_string = " ".join(event_list)
    else:
        event_string = None

    if event_string:
        types = ["health"]
        if cat.dead:
            types.append("birth_death")
        game.cur_events_list.append(
            EventInformation(event_string, types, cat_dict=cat_dict)
        )

    if not cat.dead:
        _determine_retirement(cat)


def _check_risks_and_progressions(cat, condition, conditions_to_remove):
    current_temp_conditions = {c.name for c in cat.temporary_conditions}
    current_perm_conditions = {c.name for c in cat.permanent_conditions}
    # CHECK RISKS
    for risk, chance in condition.risks.items():
        if risk in cat.temporary_conditions:
            # don't double up
            continue

        risk_progressions = TEMPORARY_CONDITIONS[risk]["progression"].keys()
        if set(risk_progressions).intersection(current_temp_conditions):
            # don't give them a condition that they already have a progression of
            continue

        if chance and random() <= chance:
            # set the risk chance back down to make it less likely it occurs again
            # for complications this is set to 0 to avoid annoying loops
            if TEMPORARY_CONDITIONS[risk].get("is_complication", False):
                condition.risks[risk] = 0.0
                # mark the current condition as having this complication
                condition.current_complication = risk
            else:
                condition.risks[risk] = 0.05

            # TODO: gather event strings

            gain_temporary_condition(cat, risk)

            continue
    # CHECK PROGRESSIONS
    for progression, chance in condition.progression.items():
        if progression in cat.temporary_conditions + cat.permanent_conditions:
            # don't double up
            continue

        # don't give them a condition that they already have a progression of
        if progression in TEMPORARY_CONDITIONS:
            further_progressions = TEMPORARY_CONDITIONS[progression][
                "progression"
            ].keys()
            if set(further_progressions).intersection(current_temp_conditions):
                continue
        elif progression in PERMANENT_CONDITIONS:
            further_progressions = PERMANENT_CONDITIONS[progression][
                "progression"
            ].keys()
            if set(further_progressions).intersection(current_perm_conditions):
                continue

        if chance and random() <= chance:
            # TODO: gather event strings

            if progression in TEMPORARY_CONDITIONS:
                gain_temporary_condition(cat, progression)
            elif progression in PERMANENT_CONDITIONS:
                if condition in TEMPORARY_CONDITIONS:
                    requires_scar = PERMANENT_CONDITIONS[progression]["requires_scar"]
                    scar_pool = (
                        condition.possible_scars
                        + PERMANENT_CONDITIONS[progression]["possible_scars"]
                    )
                    # if the condition is going from temp to perm, try to give a scar
                    event = _attempt_scarring(
                        cat,
                        condition,
                        possible_scars=scar_pool,
                        guarantee_scar=requires_scar,
                    )

                    if requires_scar and not event:
                        # if the cat couldn't be scarred for some reason, but the condition required it
                        # then we're gonna continue before we can give the condition
                        continue

                    event = event_text_adjust(Cat, event, main_cat=cat)

                gain_permanent_condition(cat, progression)

            conditions_to_remove.append(condition)

    return conditions_to_remove


def _get_valid_string_from_list(event_list: list[str], cat: Cat) -> str:
    med_cats = find_alive_cats_with_rank(
        Cat, [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE], working=True
    )

    allowed_events = []
    for event in event_list:
        if "r_c" in event:
            if med_cats:
                allowed_events.append(event)
        else:
            allowed_events.append(event)

    return event_text_adjust(
        Cat,
        choice(allowed_events),
        main_cat=cat,
        random_cat=choice(med_cats) if med_cats else None,
    )


def _determine_retirement(cat):
    # TODO: need cleanup
    if get_clan_setting("retirement") or cat.no_retire:
        return

    if cat.status.rank in (CatRank.APPRENTICE, CatRank.WARRIOR):
        for condition in cat.permanent_condition:
            if cat.permanent_condition[condition]["severity"] not in (
                "major",
                "severe",
            ):
                continue

            if cat.permanent_condition[condition]["severity"] == "severe":
                # Higher chances for "severe". These are meant to be nearly 100% without
                # being 100%
                retire_chances = {
                    CatAge.NEWBORN: 0,
                    CatAge.KITTEN: 0,
                    CatAge.ADOLESCENT: 50,  # This is high so instances where a cat retires the same moon they become an apprentice is rare
                    CatAge.YOUNG_ADULT: 10,
                    CatAge.ADULT: 5,
                    CatAge.SENIOR_ADULT: 5,
                    CatAge.SENIOR: 5,
                }
            else:
                retire_chances = {
                    CatAge.NEWBORN: 0,
                    CatAge.KITTEN: 0,
                    CatAge.ADOLESCENT: 100,
                    CatAge.YOUNG_ADULT: 80,
                    CatAge.ADULT: 70,
                    CatAge.SENIOR_ADULT: 50,
                    CatAge.SENIOR: 10,
                }

            chance = int(retire_chances.get(cat.age))
            if not int(random.random() * chance):
                retire_involved = [cat.ID]
                cat_dict = {"m_c": cat}
                if cat.age == CatAge.ADOLESCENT:
                    event = i18n.t(
                        "hardcoded.condition_retire_adolescent", name=cat.name
                    )
                elif game.clan.leader is not None:
                    if game.clan.leader.status.alive_in_player_clan and cat.moons < 120:
                        retire_involved.append(game.clan.leader.ID)
                        event = i18n.t("hardcoded.condition_retire_normal")
                    else:
                        event = i18n.t("hardcoded.condition_retire_no_leader")
                else:
                    event = i18n.t("hardcoded.condition_retire_no_leader")

                if cat.age == CatAge.ADOLESCENT:
                    event += i18n.t(
                        "hardcoded.condition_retire_adolescent_ceremony",
                        clan=game.clan.name,
                        newname=cat.name.prefix + cat.name.suffix,
                    )

                cat.retire_cat()
                # Don't add this to the condition event list: instead make it its own event, a ceremony.
                game.cur_events_list.append(
                    EventInformation(
                        event_text_adjust(Cat, event, main_cat=cat),
                        ["ceremony"],
                        retire_involved,
                        cat_dict=cat_dict,
                    )
                )


def _attempt_scarring(
    cat: Cat,
    condition: TemporaryCondition,
    possible_scars: list,
    guarantee_scar: bool = False,
) -> Optional[str]:
    if not condition.possible_scars or len(cat.pelt.scars) >= 4:
        return None

    # scar chance increased by num of moons with the condition
    if guarantee_scar:
        chance = 1
    else:
        moons_with = game.clan.age - condition.moon_gained
        chance = max(5 - moons_with, 1)

    if not int(random() * chance):
        scar_pool = possible_scars
        scar_conflicts = get_config("cat_sprites.scar_conflicts")

        for scar, conflicts in scar_conflicts.items():
            if scar in cat.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in conflicts]

        if not scar_pool:
            return None
    else:
        return None

    # If we've reached this point, we can move forward with giving history.
    cat.history.add_scar(
        i18n.t(
            "cat.history.scar_from_injury",
            injury_name=i18n.t(f"conditions.temporary_conditions.{condition.name}"),
        ),
        condition=condition.name,
    )

    # pick the scar
    scar = choice(scar_pool)

    # remove acc if need be
    if scar in ("NOTAIL", "HALFTAIL"):
        cat.pelt.accessory = tuple(
            acc
            for acc in cat.pelt.accessory
            if acc
            not in (
                "RED FEATHERS",
                "BLUE FEATHERS",
                "JAY FEATHERS",
                "GULL FEATHERS",
                "SPARROW FEATHERS",
                "CLOVER",
                "DAISY",
            )
        )

    # combining left/right variations into the both version
    if "NOLEFTEAR" in cat.pelt.scars and scar == "NORIGHTEAR":
        cat.pelt.scars = tuple(scar for scar in cat.pelt.scars if scar != "NOLEFTEAR")
        scar = "NOEAR"
    elif "NORIGHTEAR" in cat.pelt.scars and scar == "NOLEFTEAR":
        cat.pelt.scars = tuple(scar for scar in cat.pelt.scars if scar != "NORIGHTEAR")
        scar = "NOEAR"

    if "RIGHTBLIND" in cat.pelt.scars and scar == "LEFTBLIND":
        cat.pelt.scars = tuple(scar for scar in cat.pelt.scars if scar != "RIGHTBLIND")
        scar = "BOTHBLIND"
    elif "LEFTBLIND" in cat.pelt.scars and scar == "RIGHTBLIND":
        cat.pelt.scars = tuple(scar for scar in cat.pelt.scars if scar != "LEFTBLIND")
        scar = "BOTHBLIND"

    # give scar to cat
    cat.pelt.scars = (*cat.pelt.scars, scar)

    # find string
    scar_gain_strings = [
        "hardcoded.scar_event0",
        "hardcoded.scar_event1",
        "hardcoded.scar_event2",
    ]

    return i18n.t(
        choice(scar_gain_strings),
        injury=i18n.t(f"conditions.temporary_conditions.{condition.name}"),
    )
