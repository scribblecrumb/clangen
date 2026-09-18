import logging
import random

from scripts.cat.cats import Cat
from scripts.cat.conditions.gain_conditions import gain_temporary_condition
from scripts.cat.enums import CatRank
from scripts.clan_package.settings import get_clan_setting
from scripts.clan_resources.freshkill import (
    FRESHKILL_ACTIVE,
    MAL_PERCENTAGE,
    STARV_PERCENTAGE,
)
from scripts.config import get_config
from scripts.events_module.condition.condition_events import generate_condition_event
from scripts.events_module.short.short_event_generation import create_short_event
from scripts.game_structure import constants
from scripts.game_structure import game
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
)

logger = logging.getLogger(__name__)

def handle_nutrient(cat: Cat, nutrition_info: dict) -> None:
    """
    Handles gaining conditions or death for cats with low nutrient.
    This function should only be called if the game is in 'expanded' or 'cruel_season' mode.

    Starvation and malnutrtion must be handled separately from other illnesses due to their distinct death triggers.

        Parameters
        ----------
        cat : Cat
            the cat which has to be checked and updated
        nutrition_info : dict
            dictionary of all nutrition information (can be found in the freshkill pile)
    """
    if not FRESHKILL_ACTIVE:
        return

    if cat.ID not in nutrition_info.keys():
        logger.error(
            "Could not find cat with ID %s (%s) in the nutrition information.",
            cat.ID,
            str(cat.name),
        )
        return

    # get all events for a certain rank of a cat
    cat_nutrition = nutrition_info[cat.ID]

    event = None
    illness = None
    heal = False

    # handle death first, if percentage is 0 or lower, the cat will die
    if cat_nutrition.percentage <= 0:
        event = generate_condition_event(
            path="conditions/death_strings/starving", involved_cats={"m_c": cat}
        )
        # if the cat is the leader and isn't full dead
        # make them malnourished and refill nutrition slightly
        if cat.status.is_leader and game.clan.leader_lives > 0:
            mal_score = (
                nutrition_info[cat.ID].max_score / 100 * (MAL_PERCENTAGE + 1)
            )
            nutrition_info[cat.ID].current_score = round(mal_score, 2)
            gain_temporary_condition(cat, "malnourished")

        game.cur_events_list.append(event)
        return

    # heal cat if percentage is high enough and cat is ill
    if (
        cat_nutrition.percentage > MAL_PERCENTAGE
        and "malnourished" in cat.temporary_conditions
    ):
        heal = True

    # heal cat if percentage is high enough and cat is ill
    elif (
        cat_nutrition.percentage > STARV_PERCENTAGE
        and "starving" in cat.temporary_conditions
    ):
        if cat_nutrition.percentage < MAL_PERCENTAGE:
            if "malnourished" not in cat.temporary_conditions:
                gain_temporary_condition(cat, "malnourished")
            illness = "starving"
            heal = True
        else:
            illness = "starving"
            heal = True

    elif MAL_PERCENTAGE >= cat_nutrition.percentage > STARV_PERCENTAGE:
        # because of the smaller 'nutrition buffer', kitten and elder should get the starving condition.
        if cat.status.rank in (CatRank.KITTEN, CatRank.ELDER):
            illness = "starving"
        else:
            illness = "malnourished"

    elif cat_nutrition.percentage <= STARV_PERCENTAGE:
        illness = "starving"

    # handle the gaining/healing illness
    if heal:
        event = generate_condition_event(
            path=f"conditions/healed_strings/{illness}", involved_cats={"m_c": cat}
        )
        cat.remove_condition(illness)
    elif not heal and illness:
        event = generate_condition_event(
            path=f"conditions/gain_temporary_condition_strings/{illness}",
            involved_cats={"m_c": cat},
        )
        gain_temporary_condition(cat, illness)

    if event:
        game.cur_events_list.append(event)

def handle_illnesses(cat, season=None):
    """
    This function handles the illnesses overall by randomly making cat ill (or not).
    It will return a bool to indicate if the cat is dead.
    """
    # return immediately if they're already dead
    triggered = False
    if cat.dead:
        if cat.dead:
            triggered = True
        return triggered

    event = None

    # ---------------------------------------------------------------------------- #
    #                              make cats sick                                  #
    # ---------------------------------------------------------------------------- #

    path = (
        "condition_related.classic_illness_chance"
        if game.clan.game_mode == "classic"
        else "condition_related.illness_chance"
    )
    random_number = int(random.random() * get_config(path))
    if not cat.dead and not cat.temporary_conditions and random_number <= 10:
        # CLAN FOCUS!
        if get_clan_setting("rest_and_recover"):
            stopping_chance = constants.CONFIG["focus"]["rest_and_recover"][
                "illness_prevent"
            ]
            if not int(random.random() * stopping_chance):
                return triggered

        season_dict = get_config(
            f"condition_related.seasonal_chances.{season.casefold()}"
        )
        possible_illnesses = []

        # pick up possible illnesses from the season dict
        for illness_name in season_dict:
            possible_illnesses += [illness_name] * season_dict[illness_name]

        # pick a random illness from those possible
        random_index = int(random.random() * len(possible_illnesses))
        chosen_illness = possible_illnesses[random_index]
        # if a non-kitten got kittencough, switch it to whitecough instead
        if chosen_illness == "kittencough" and not cat.status.rank.is_baby():
            chosen_illness = "whitecough"

        # create event text
        event = generate_condition_event(
            f"conditions/gain_temporary_condition_strings/{chosen_illness}",
            {"m_c": cat},
        )

        # make em sick
        gain_temporary_condition(cat, chosen_illness)

    # if an event happened, then add event to cur_event_list and save death if it happened.
    if event:
        game.cur_events_list.append(event)

    # just double-checking that trigger is only returned True if the cat is dead
    if cat.dead:
        triggered = True
    else:
        triggered = False

    return triggered

def handle_injuries(cat, random_cat=None):
    """
    This function handles injuries overall by randomly injuring cat (or not).
    Returns: boolean - if an event was triggered
    """
    triggered = False

    modify_for_war = (
        game.clan.war["at_war"]
        and switch_get_value(Switch.war_rel_change_type) != "rel_up"
    )
    path = (
        "condition_related.classic_injury_chance"
        if game.clan.game_mode == "classic"
        else "condition_related.injury_chance"
    )

    injury_chance = get_config(path) - (
        get_config("condition_related.war_injury_modifier") if modify_for_war else 0
    )

    random_number = int(random.random() * injury_chance)

    if cat.dead:
        triggered = True
        return triggered

    if (
        constants.CONFIG["event_generation"]["debug_type_override"] == "injury"
        and random_cat
    ):
        create_short_event(
            event_type="health",
            main_cat=cat,
            random_cat=random_cat,
        )

    else:
        # EVENTS
        if (
            not triggered
            and cat.personality.trait
            in (
                "adventurous",
                "bold",
                "daring",
                "confident",
                "ambitious",
                "bloodthirsty",
                "fierce",
                "strict",
                "troublesome",
                "vengeful",
                "impulsive",
            )
            and random_number <= 15
        ):
            triggered = True
        elif not triggered and random_number <= 5:
            triggered = True

        if triggered:
            # CLAN FOCUS!
            if get_clan_setting("rest_and_recover"):
                stopping_chance = constants.CONFIG["focus"]["rest_and_recover"][
                    "injury_prevent"
                ]
                if not int(random.random() * stopping_chance):
                    return False

            create_short_event(
                event_type="health",
                main_cat=cat,
                random_cat=random_cat,
            )

    # just double-checking that trigger is only returned True if the cat is dead
    if cat.status.rank != CatRank.LEADER:
        # only checks for non-leaders, as leaders will not be dead if they are just losing a life
        if cat.dead:
            triggered = True
        else:
            triggered = False

    return triggered
