import re
from random import getrandbits, randint, choice, choices
from typing import List, Optional, Dict

import i18n

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.enums import CatRank, CatAge, CatSocial, CatGroup, CatStanding
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure import game, constants


def generate_new_cat(
    event,
    in_event_cats: Dict[str, Cat],
    new_cat_index: int,
    attribute_list: List[str],
    other_clan=None,
) -> list:
    """
    Generates new cats based off attribute list
    """

    # PARENTAL INDEXES
    parent1, parent2, adoptive_parents = _get_parent_indexes(
        attribute_list, event, in_event_cats, new_cat_index
    )

    # MATE INDEXES
    mate_indexes = _get_mate_indexes(attribute_list, in_event_cats)

    # GENDER
    gender = _get_gender_tag(attribute_list)

    # NAME
    needs_new_name = _get_name_status(attribute_list)

    # GROUP
    cat_social, cat_group = _get_cat_social_and_group(attribute_list, other_clan)

    # RANK AND AGE - must be handled at this point in the sequence
    rank, moon_age = _get_rank_and_age(attribute_list, mate_indexes)

    # MEETING
    if "meeting" in attribute_list:
        joining = False
        if cat_social not in ("former clancat", CatSocial.CLANCAT):
            rank = None
    else:
        joining = True

    # BACKSTORIES
    possible_stories, chosen_backstory, cat_social, cat_group = _get_backstory(
        attribute_list, cat_social, cat_group, rank
    )

    # LITTER
    if "litter" in attribute_list:
        litter = True
        if rank not in (CatRank.KITTEN, CatRank.NEWBORN):
            # if we tagged an incorrect rank, there's a problem
            raise Exception(
                f"{attribute_list} included a litter tag, but also had a conflicting rank tag."
            )
    else:
        litter = False

    # IS THE CAT DEAD?
    if "dead" in attribute_list:
        alive = False
    else:
        alive = True

    # check if we can use an existing cat here
    if "exists" in attribute_list:
        if "litter" in attribute_list:
            raise Exception(
                f"{attribute_list} has both the litter and exists tag, these can't coexist."
            )

        existing_outsiders = [
            i for i in Cat.all_cats.values() if i.status.is_outsider and not i.dead
        ]
        possible_outsiders = []

        # find any qualified outsiders
        for cat in existing_outsiders:
            if cat.backstory not in possible_stories:
                continue
            if cat_social != cat.status.social or (
                cat_social == "former clancat" and not cat.status.is_former_clancat
            ):
                continue
            if cat_group != cat.status.group_ID:
                continue
            if gender and gender != cat.gender:
                continue
            if moon_age and moon_age not in Cat.age_moons[cat.age]:
                continue
            possible_outsiders.append(cat)

        # if we have any qualified outsiders
        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            _handle_use_of_existing_cat(
                alive, chosen_cat, joining, needs_new_name, rank
            )

            return [chosen_cat]

    # if we didn't find an appropriate existing cat, we generate one
    new_cats: list = []

    return new_cats


def _create_litter(
    backstory: str,
    joining: bool,
    moon_age: int,
    parent1: str,
    parent2: str,
    adoptive_parents: List[str],
    original_social: Optional[CatSocial],
    original_group: Optional[str],
) -> list[Cat]:
    """
    Creates a litter of kittens.
    """
    litter_size = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if not moon_age:
        moon_age = randint(1, 5)

    if moon_age == 0:
        age = CatAge.NEWBORN
    else:
        age = CatAge.KITTEN

    # if we don't know our social, then we copy a parent
    if not original_social and parent1:
        original_social = Cat.fetch_cat(parent1).status.social
    if not original_group and parent1:
        original_group = Cat.fetch_cat(parent1).status.group_ID

    for baby in range(litter_size):
        new_cat = Cat(
            moons=moon_age,
            status_dict={
                "social": original_social,
                "age": age,
                "group_ID": original_group,
            },
            backstory=backstory,
            parent=parent1,
            parent2=parent2,
            adoptive_parents=adoptive_parents if adoptive_parents else [],
        )
        new_cat.status.change_current_moons_as(moon_age)

        if joining:
            # add to clan
            new_cat.status.add_to_group(CatGroup.PLAYER_CLAN_ID, age)
            new_cat.add_to_clan()

            # change name
            new_cat.change_name()

            # perm conditions
            chance_for_perm_condition = int(
                constants.CONFIG["cat_generation"]["base_permanent_condition"] / 11.25
            )


def _handle_use_of_existing_cat(alive, chosen_cat, joining, needs_new_name, rank):
    if not alive:
        chosen_cat.die()

    elif joining:
        # find a rank appropriate for age
        if not rank:
            rank = chosen_cat.status.get_rank_from_age(chosen_cat.age)
        # add to the clan!
        chosen_cat.add_to_clan()
        # change rank
        if chosen_cat.status.rank != rank:
            chosen_cat.rank_change(new_rank=CatRank(rank), resort=True)
        # change name
        if needs_new_name:
            if bool(getrandbits(1)):
                chosen_cat.name.give_partial_clan_name()
            else:  # completely new name
                chosen_cat.name.give_clan_name()

    elif not joining:
        # updates so that the clan is marked as knowing of this cat
        current_standing = chosen_cat.status.get_standing_with_group(
            CatGroup.PLAYER_CLAN_ID
        )
        if (
            CatStanding.KNOWN not in current_standing
            and CatStanding.EXILED not in current_standing
        ):
            chosen_cat.status.change_standing(CatStanding.KNOWN)


def _get_name_status(attribute_list) -> bool:
    if "new_name" in attribute_list:
        return True
    elif "old_name" in attribute_list:
        return False
    elif "meeting" in attribute_list:
        return False
    else:
        return bool(getrandbits(1))


def _get_gender_tag(attribute_list) -> Optional[str]:
    if "male" in attribute_list:
        return "male"
    elif "female" in attribute_list:
        return "female"
    elif "can_birth" in attribute_list and not get_clan_setting("same sex birth"):
        return "female"
    else:
        return None


def _get_backstory(attribute_list, cat_social, cat_group, rank) -> (str, CatSocial):
    chosen_backstory, cat_social = _check_if_backstory_tagged(
        attribute_list, cat_social
    )

    # if no backstory was specified, we pick one based off rank/social or just assign and random one
    if not chosen_backstory:
        if rank in (CatRank.KITTEN, CatRank.NEWBORN):
            chosen_backstory = choice(
                BACKSTORIES["backstory_categories"]["abandoned_backstories"]
            )
        elif rank == CatRank.MEDICINE_CAT and cat_social == CatSocial.CLANCAT:
            chosen_backstory = choice(["medicine_cat", "disgraced1"])
        elif rank == CatRank.MEDICINE_CAT:
            chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
        else:
            if cat_social == CatSocial.CLANCAT:
                x = "former_clancat"
            else:
                x = cat_social
            chosen_backstory = choice(
                BACKSTORIES["backstory_categories"].get(
                    f"{x}_backstories", ["outsider1"]
                )
            )

    # this is just a little double check in case we randomly gave a clancat backstory but don't have a group
    if not cat_group and (
        chosen_backstory
        in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            + BACKSTORIES["backstory_categories"]["baby_clancat_backstories"]
        )
        or cat_social == "former clancat"
    ):
        cat_group = choice([x.group_ID for x in game.clan.all_other_clans])

    return chosen_backstory, cat_social, cat_group


def _check_if_backstory_tagged(attribute_list, cat_social) -> (list, str, CatSocial):
    possible_stories = []

    # find any backstory tags
    all_stories = set(
        [
            backstory
            for backstory_block in BACKSTORIES["backstory_categories"].values()
            for backstory in backstory_block
        ]
    )
    for _tag in attribute_list:
        match = re.match(r"backstory:(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            for story in bs_list:
                if story in all_stories:
                    possible_stories.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    possible_stories.extend(BACKSTORIES["backstory_categories"][story])
            break

    if not possible_stories:
        return None, cat_social

    # pick backstory
    chosen_backstory = choice(possible_stories)

    # we have to ensure the social matches up with the new backstory
    if chosen_backstory in (
        BACKSTORIES["backstory_categories"]["baby_clancat_backstories"]
        + BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
    ):
        cat_social = CatSocial.CLANCAT
    elif chosen_backstory in (
        BACKSTORIES["backstory_categories"]["baby_loner_backstories"]
        + BACKSTORIES["backstory_categories"]["loner_backstories"]
    ):
        cat_social = CatSocial.LONER
    elif chosen_backstory in (
        BACKSTORIES["backstory_categories"]["baby_kittypet_backstories"]
        + BACKSTORIES["backstory_categories"]["kittypet_backstories"]
    ):
        cat_social = CatSocial.KITTYPET
    elif chosen_backstory in BACKSTORIES["backstory_categories"]["rogue_backstories"]:
        cat_social = CatSocial.ROGUE

    return possible_stories, chosen_backstory, cat_social


def _get_cat_social_and_group(attribute_list, other_clan) -> (Optional[CatSocial], str):
    cat_group = None

    if "kittypet" in attribute_list:
        cat_social = CatSocial.KITTYPET
    elif "rogue" in attribute_list:
        cat_social = CatSocial.ROGUE
    elif "loner" in attribute_list:
        cat_social = CatSocial.LONER
    elif "clancat" in attribute_list or "former clancat" in attribute_list:
        # assign social
        if "former clancat" in attribute_list:
            # this isn't a real social, but it informs us of how to handle this cat later on
            cat_social = "former clancat"
        else:
            cat_social = CatSocial.CLANCAT

        # assign group
        if other_clan:
            cat_group = other_clan.group_ID
        else:
            cat_group = choice([x.group_ID for x in game.clan.all_other_clans])
    else:
        # if no social tag was given, we just pick an outsider one willynilly
        cat_social = choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])

    return cat_social, cat_group


def _get_rank_and_age(attribute_list, mate_indexes) -> (CatRank, int):
    rank = _get_rank(attribute_list)
    moon_age = _get_moon_age(attribute_list, mate_indexes)

    if rank and not moon_age:
        # in this case, we need to ensure the cat takes an appropriate age for their rank
        if rank in (
            CatRank.APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
        ):
            moon_age = randint(
                Cat.age_moons[CatAge.ADOLESCENT][0],
                Cat.age_moons[CatAge.ADOLESCENT][1],
            )
        elif rank in (CatRank.WARRIOR, CatRank.MEDIATOR, CatRank.MEDICINE_CAT):
            moon_age = randint(
                Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1]
            )
        elif rank == CatRank.ELDER:
            moon_age = randint(Cat.age_moons["senior"][0], Cat.age_moons["senior"][1])

    return rank, moon_age


def _get_moon_age(attribute_list, mate_indexes) -> Optional[int]:
    for _tag in attribute_list:
        match = re.match(r"age:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            min_age, max_age = Cat.age_moons[CatAge(match.group(1))]
            return randint(min_age, max_age)

        # Set same as first mate
        if match.group(1) == "mate" and mate_indexes:
            min_age, max_age = Cat.age_moons[mate_indexes[0].age]
            return randint(min_age, max_age)

        if match.group(1) == "has_kits":
            return randint(19, 120)

    return None


def _get_rank(attribute_list) -> Optional[CatRank]:
    for _tag in attribute_list:
        match = re.match(r"status:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in [
            CatRank.NEWBORN,
            CatRank.KITTEN,
            CatRank.ELDER,
            CatRank.APPRENTICE,
            CatRank.WARRIOR,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDIATOR,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDICINE_CAT,
        ]:
            return match.group(1)

    return None


def _get_mate_indexes(attribute_list, in_event_cats) -> List[Cat]:
    mate_indexes = []
    for tag in attribute_list:
        match = re.match(r"mate:([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        for index in mate_indexes:
            if index not in in_event_cats:
                raise Exception(
                    f"{tag} is attached to an index that doesn't exist in the event."
                )

            if in_event_cats[index].status.rank.is_any_apprentice_rank():
                raise Exception(
                    f"{tag} is attached to an apprentice's index but apprentices can't be given mates."
                )

            mate_indexes.append(in_event_cats[index])

    return mate_indexes


def _get_parent_indexes(
    attribute_list, event, in_event_cats, new_cat_index
) -> (str, str, List[str]):
    parent1 = None
    parent2 = None
    adoptive_parents = []
    for tag in attribute_list:
        # finding parent tags
        parent_match = re.match(r"parent:([,0-9]+)", tag)
        adoptive_match = re.match(r"adoptive:(.+)", tag)
        if not parent_match and not adoptive_match:
            # check next tag if this isn't a parent tag
            continue

        # find the index for the parents
        parent_indexes = parent_match.group(1).split(",") if parent_match else []
        adoptive_indexes = adoptive_match.group(1).split(",") if adoptive_match else []
        if not parent_indexes and not adoptive_indexes:
            # something is wrong if we had a parent tag but no indexes attached
            raise Exception(f"Error: {tag} in new_cat block is missing parent indexes.")

        parent_indexes = [int(index) for index in parent_indexes]
        for index in parent_indexes:
            if index >= new_cat_index:
                # something is wrong if this index is greater or the same as the current new_cat_index
                raise Exception(
                    f"Error: {tag} in new_cat block has the wrong index or the block is mis-ordered. Parents must always be created first."
                )

            if parent1 is None:
                parent1 = event.new_cats[index][0]
            else:
                parent2 = event.new_cats[index][0]

        # find the index for the adoptive parents
        adoptive_indexes = [
            int(index) if index.isdigit() else index for index in adoptive_indexes
        ]
        for index in adoptive_indexes:
            # add listed adoptive parent as well as their mates
            if in_event_cats[index].ID not in adoptive_parents:
                adoptive_parents.append(in_event_cats[index].ID)
                adoptive_parents.extend(in_event_cats[index].mate)

    return parent1, parent2, adoptive_parents
