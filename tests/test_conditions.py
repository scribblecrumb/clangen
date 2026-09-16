import unittest

from scripts.cat.conditions.condition_state import ConditionState
from scripts.cat.conditions.coverage_check import medicine_cats_can_cover_clan
from scripts.cat.conditions.gain_conditions import (
    gain_temporary_condition,
    gain_permanent_condition,
)
from scripts.cat.constants import TEMPORARY_CONDITIONS, PERMANENT_CONDITIONS
from scripts.cat.enums import CatRank
from scripts.cat.factories.test_cat_factory import TestCatFactory
from scripts.events_module.condition.condition_events import handle_temporary_conditions

cat_factory = TestCatFactory()


class TestsMedCondition(unittest.TestCase):
    def test_fulfilled(self):
        cat1 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )
        med = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.MEDICINE_CAT},
            disable_random=True,
        )

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats))

    def test_fulfilled_many_cats(self):
        cat1 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )
        cat2 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )
        cat3 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )
        cat4 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )

        med1 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.MEDICINE_CAT},
            disable_random=True,
        )
        med2 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.MEDICINE_CAT},
            disable_random=True,
        )

        all_cats = [cat1, cat2, cat3, cat4, med1, med2]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats))

    def test_injured_fulfilled(self):
        cat1 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )

        med = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.MEDICINE_CAT},
            disable_random=True,
        )
        gain_temporary_condition(med, "small_cut")

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats))

    def test_illness_fulfilled(self):
        cat1 = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.WARRIOR},
            disable_random=True,
        )

        med = cat_factory.create_cat(
            moons=20,
            status_dict={"rank": CatRank.MEDICINE_CAT},
            disable_random=True,
        )
        gain_temporary_condition(med, "running_nose")

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats))


class TestTemporaryCondition(unittest.TestCase):
    def test_gain(self):
        for c in TEMPORARY_CONDITIONS:
            with self.subTest(f"Test gain {c}"):
                cat1 = cat_factory.create_cat()
                gain_temporary_condition(cat1, c, allow_side_effects=False)

                self.assertTrue(
                    c in cat1.temporary_conditions,
                    msg=f"{c} was not in {cat1.temporary_conditions}",
                )



class TestPermanentCondition(unittest.TestCase):
    def test_gain(self):
        for c in PERMANENT_CONDITIONS:
            with self.subTest(f"Test gain {c}"):
                congenital = PERMANENT_CONDITIONS[c]["can_be_congenital"]
                acquired = PERMANENT_CONDITIONS[c]["can_be_acquired"]

                if congenital:
                    cat1 = cat_factory.create_cat()
                    gain_permanent_condition(cat1, c, is_congenital=True)

                    self.assertTrue(
                        c in cat1.permanent_conditions,
                        msg=f"{c} (congenital) was not in {cat1.permanent_conditions}",
                    )
                    self.assertTrue(
                        cat1.get_condition(c).is_congenital,
                        msg=f"{c} (congenital) was not marked as congenital.",
                    )

                if acquired:
                    cat1 = cat_factory.create_cat()
                    gain_permanent_condition(cat1, c, is_congenital=False)

                    self.assertTrue(
                        c in cat1.permanent_conditions,
                        msg=f"{c} (acquired) was not in {cat1.permanent_conditions}",
                    )
                    self.assertFalse(
                        cat1.get_condition(c).is_congenital,
                        msg=f"{c} (acquired) was marked as congenital.",
                    )
