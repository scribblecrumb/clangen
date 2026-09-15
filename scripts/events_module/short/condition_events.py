import logging
import random
from typing import Dict, List

import i18n

from scripts.cat.cats import Cat
from scripts.cat.conditions.conditions import (
    gain_temporary_condition,
    gain_permanent_condition,
)
from scripts.cat.constants import TEMPORARY_CONDITIONS
from scripts.cat.enums import CatRank
from scripts.clan_package.settings import get_clan_setting
from scripts.clan_resources.freshkill import (
    FRESHKILL_ACTIVE,
    MAL_PERCENTAGE,
    STARV_PERCENTAGE,
)
from scripts.config import get_config
from scripts.events_module.consequences import check_stolen_vitality
from scripts.events_module.event_information import EventInformation
from scripts.events_module.short.short_event_generation import create_short_event
from scripts.events_module.text_adjust import event_text_adjust, get_leader_life_notice
from scripts.game_structure import constants
from scripts.game_structure import game
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
)
from scripts.game_structure.localization import load_lang_resource

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------- #
#                             Condition Event Class                            #
# ---------------------------------------------------------------------------- #


class Condition_Events:
    """All events with a connection to conditions."""

    resource_directory = "resources/dicts/conditions/"
    current_loaded_lang = None

    # ---------------------------------------------------------------------------- #
    #                                   STRINGS                                    #
    # ---------------------------------------------------------------------------- #

    PERM_CONDITION_RISK_STRINGS: Dict[str, Dict[str, List[str]]] = {}
    ILLNESS_RISK_STRINGS: Dict[str, Dict[str, List[str]]] = {}
    INJURY_RISK_STRINGS: Dict[str, Dict[str, List[str]]] = {}
    CONGENITAL_CONDITION_GOT_STRINGS: Dict[str, List[str]] = {}
    PERMANENT_CONDITION_GOT_STRINGS: Dict[str, List[str]] = {}
    ILLNESS_GOT_STRINGS: Dict[str, List[str]] = {}
    ILLNESS_HEALED_STRINGS: Dict[str, List[str]] = {}
    INJURY_HEALED_STRINGS: Dict[str, List[str]] = {}
    INJURY_DEATH_STRINGS: Dict[str, List[str]] = {}
    ILLNESS_DEATH_STRINGS: Dict[str, List[str]] = {}

    @classmethod
    def rebuild_strings(cls):
        if cls.current_loaded_lang == i18n.config.get("locale"):
            return

        resources = [
            (
                "PERM_CONDITION_RISK_STRINGS",
                "risk_strings/permanent_condition_risk_strings.json",
            ),
            ("ILLNESS_RISK_STRINGS", "risk_strings/illness_risk_strings.json"),
            ("INJURY_RISK_STRINGS", "risk_strings/injuries_risk_strings.json"),
            (
                "CONGENITAL_CONDITION_GOT_STRINGS",
                "condition_got_strings/gain_congenital_condition_strings.json",
            ),
            (
                "PERMANENT_CONDITION_GOT_STRINGS",
                "condition_got_strings/gain_permanent_condition_strings.json",
            ),
            ("ILLNESS_GOT_STRINGS", "condition_got_strings/gain_illness_strings.json"),
            (
                "ILLNESS_HEALED_STRINGS",
                "healed_and_death_strings/illness_healed_strings.json",
            ),
            (
                "INJURY_HEALED_STRINGS",
                "healed_and_death_strings/injury_healed_strings.json",
            ),
            (
                "INJURY_DEATH_STRINGS",
                "healed_and_death_strings/injury_death_strings.json",
            ),
            (
                "ILLNESS_DEATH_STRINGS",
                "healed_and_death_strings/illness_death_strings.json",
            ),
        ]

        for class_property, file in resources:
            setattr(cls, class_property, load_lang_resource(f"conditions/{file}"))

        cls.current_loaded_lang = i18n.config.get("locale")

    @staticmethod
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

        Condition_Events.rebuild_strings()

        # handle death first, if percentage is 0 or lower, the cat will die
        if cat_nutrition.percentage <= 0:
            text = ""
            if cat.status.is_leader:
                game.clan.leader_lives -= 1
                # kill and retrieve leader life text
                text = get_leader_life_notice(cat.name)
                if extra_text := check_stolen_vitality(cat, 1):
                    text += " " + extra_text

            possible_string_list = Condition_Events.ILLNESS_DEATH_STRINGS["starving"]
            event = random.choice(possible_string_list) + " " + text
            # first event in string lists is always appropriate for history formatting
            history_event = possible_string_list[0]

            event = event_text_adjust(Cat, event.strip(), main_cat=cat)

            cat.history.add_death(
                condition="starving", death_text=history_event.strip()
            )

            cat.die()

            # if the cat is the leader and isn't full dead
            # make them malnourished and refill nutrition slightly
            if cat.status.is_leader and game.clan.leader_lives > 0:
                mal_score = (
                    nutrition_info[cat.ID].max_score / 100 * (MAL_PERCENTAGE + 1)
                )
                nutrition_info[cat.ID].current_score = round(mal_score, 2)
                gain_temporary_condition(cat, "malnourished")

            types = ["birth_death"]
            game.cur_events_list.append(
                EventInformation(event, types, cat_dict={"m_c": cat})
            )
            return

        # heal cat if percentage is high enough and cat is ill
        if (
            cat_nutrition.percentage > MAL_PERCENTAGE
            and "malnourished" in cat.temporary_conditions
        ):
            illness = "malnourished"
            event = random.choice(
                Condition_Events.ILLNESS_HEALED_STRINGS["malnourished"]
            )
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
            event = random.choice(Condition_Events.ILLNESS_HEALED_STRINGS[illness])
            cat.temporary_conditions.pop(illness)
        elif not heal and illness:
            event = random.choice(Condition_Events.ILLNESS_GOT_STRINGS[illness])
            gain_temporary_condition(cat, illness)

        if event:
            event_text = event_text_adjust(Cat, event, main_cat=cat)
            types = ["health"]
            game.cur_events_list.append(
                EventInformation(event_text, types, cat_dict={"m_c": cat})
            )

    @staticmethod
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

        event_string = None
        cat_dict = {"m_c": cat}

        # ---------------------------------------------------------------------------- #
        #                              make cats sick                                  #
        # ---------------------------------------------------------------------------- #

        path = (
            "condition_related.classic_illness_chance"
            if game.clan.game_mode == "classic"
            else "condition_related.illness_chance"
        )
        random_number = int(random.random() * get_config(path))
        if (
            not cat.dead
            and not cat.is_ill()
            and random_number <= 10
            and not event_string
        ):
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
            try:
                event_string = random.choice(
                    Condition_Events.ILLNESS_GOT_STRINGS[chosen_illness]
                )
            except KeyError:
                # try to translate the illness
                chosen_illness = i18n.t(f"conditions.illnesses.{chosen_illness}")

                event_string = i18n.t(
                    "defaults.illness_get_event",
                    illness=chosen_illness,
                )
                # just in case we couldn't translate it
                event_string.replace("conditions.illnesses.", "")

            # make em sick
            gain_temporary_condition(cat, chosen_illness)

            event_string = event_text_adjust(Cat, text=event_string, main_cat=cat)

        # if an event happened, then add event to cur_event_list and save death if it happened.
        if event_string:
            types = ["health"]
            if cat.dead:
                types.append("birth_death")
            game.cur_events_list.append(
                EventInformation(event_string, types, cat_dict=cat_dict)
            )

        # just double-checking that trigger is only returned True if the cat is dead
        if cat.dead:
            triggered = True
        else:
            triggered = False

        return triggered

    @staticmethod
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


Condition_Events.rebuild_strings()
