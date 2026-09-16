import random

from scripts.cat import pronouns
from scripts.cat.cats import Cat
from scripts.cat.enums import CatAge
from scripts.config import get_config
from scripts.events_module.event_information import EventInformation
from scripts.events_module.text_pool_event.event_retrieval import (
    load_text_pool_events,
    get_valid_event,
)
from scripts.events_module.text_pool_event.handle_consequences import execute_outcome
from scripts.events_module.text_pool_event.text_pool_event import TextPoolEvent
from scripts.game_structure import game


def _generate_condition_event(main_cat: Cat, path: str):
    """
    Actually generate and execute condition event
    """
    possible_events = load_text_pool_events(path)
    involved_cats = {"m_c": main_cat}

    chosen_event, involved_cats = get_valid_event(
        primary_cat=main_cat,
        involved_cats=involved_cats,
        interactable_cats=Cat.all_cats_list,
        possible_events=possible_events,
        frequency_active=False,
    )

    # we won't use results and rel_results here
    processed_text, results, rel_results = execute_outcome(
        event=chosen_event,
        event_involved_cats=involved_cats,
    )

    game.cur_events_list.append(
        EventInformation(
            processed_text,
            ["misc"],
            [c.ID for c in involved_cats.values()],
        )
    )
