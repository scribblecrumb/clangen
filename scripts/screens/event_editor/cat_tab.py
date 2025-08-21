import pygame

from scripts.game_structure.editor_elements import EditorBlockSelection
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UITextBoxTweaked
from scripts.utility import ui_scale, get_text_box_theme


class CatTab:
    def __init__(self):
        self.param_locks = None
        self.editor_element = None
        self.editor_container = None

        self.cat_dict = {}

        self.main_cat_editor = {}

    # MAIN/RANDOM CAT EDITOR
    def generate_main_cat_tab(
        self, editor_container, editor_element, param_locks, mass_death: bool
    ):
        self.editor_container = editor_container
        self.editor_element = editor_element
        self.param_locks = param_locks

        self.main_cat_editor["intro"] = UITextBoxTweaked(
            "screens.event_edit.mass_death_info"
            if mass_death
            else "screens.event_edit.cat_info",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
        )

        self.main_cat_editor["list"] = EditorBlockSelection(
            ui_scale(pygame.Rect((12, 20), (112, 186))),
            container=self.editor_container,
            manager=MANAGER,
            item_dict=self.cat_dict,
            anchors={"left_target": self.main_cat_editor["intro"]},
        )

        # DEATH
        self.create_dies_editor(self.main_cat_editor)

        # RANK
        self.create_rank_editor()

        # AGE
        self.create_age_editor()

        # REL STATUS
        self.create_rel_status_editor()

        # SKILLS
        self.create_skill_editor()

        # TRAITS
        self.create_trait_editor()

        # BACKSTORIES
        self.create_backstory_editor()

    def create_backstory_editor(self, prev_element=None):
        prev_element = prev_element if prev_element else self.editor_element["traits"]

        self.backstory_element["text"] = UITextBoxTweaked(
            "screens.event_edit.backstory_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={"top_target": prev_element},
        )

        self.backstory_element["pools"] = UIScrollingButtonList(
            pygame.Rect((25, 20), (200, 198)),
            item_list=[pool for pool in self.all_backstories.keys()],
            button_dimensions=(200, 30),
            multiple_choice=False,
            container=self.editor_container,
            anchors={"top_target": self.backstory_element["text"]},
            manager=MANAGER,
        )
        backstory = set(self.current_cat_dict["backstory"]).intersection(
            self.all_backstories.keys()
        )
        if backstory:
            self.backstory_element["pools"].set_selected_list(list(backstory))

        self.backstory_element["frame"] = UIModifiedImage(
            ui_scale(pygame.Rect((-20, 30), (180, 170))),
            get_box(BoxStyles.ROUNDED_BOX, (180, 170)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["text"],
                "left_target": self.backstory_element["pools"],
            },
        )
        self.backstory_element["frame"].disable()
        self.backstory_element["list"] = UIScrollingButtonList(
            pygame.Rect((-4, 38), (156, 152)),
            item_list=[],
            button_dimensions=(156, 30),
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["text"],
                "left_target": self.backstory_element["pools"],
            },
            manager=MANAGER,
        )
        backstory = set(self.current_cat_dict["backstory"]).intersection(
            self.individual_stories
        )
        if backstory:
            self.backstory_element["list"].set_selected_list(list(backstory))

        self.backstory_element["display"] = UITextBoxTweaked(
            f"chosen backstories: {self.current_cat_dict['backstory']}",
            ui_scale(pygame.Rect((10, 10), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["pools"],
            },
            allow_split_dashes=False,
        )
        if self.current_cat_dict != self.selected_new_cat_info:
            label = "main" if self.current_cat_dict == self.main_cat_info else "random"
            self.create_lock(
                name=f"{label}_backstory",
                top_anchor=self.backstory_element["pools"],
                left_anchor=self.backstory_element["display"],
            )
        self.create_divider(self.backstory_element["display"], "backstory")

    def create_trait_editor(self):
        self.trait_element["text"] = UITextBoxTweaked(
            "screens.event_edit.trait_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={"top_target": self.editor_element["skills"]},
        )
        self.trait_element["allow"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((130, 10), (80, 30))),
            "allow",
            get_button_dict(ButtonStyles.MENU_LEFT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_left",
            container=self.editor_container,
            anchors={"top_target": self.trait_element["text"]},
        )
        # allow is picked by default, so this is initially disabled
        self.trait_element["allow"].disable()
        self.trait_element["exclude"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 10), (80, 30))),
            "exclude",
            get_button_dict(ButtonStyles.MENU_RIGHT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_right",
            container=self.editor_container,
            anchors={
                "left_target": self.trait_element["allow"],
                "top_target": self.trait_element["text"],
            },
        )

        self.trait_element["kitten"] = UIScrollingDropDown(
            pygame.Rect((30, 20), (140, 30)),
            dropdown_dimensions=(140, 198),
            item_list=self.kit_traits,
            parent_text="kitten traits",
            container=self.editor_container,
            anchors={"top_target": self.trait_element["allow"]},
            manager=MANAGER,
        )
        traits = set(self.current_cat_dict["trait"]).intersection(self.kit_traits)
        if traits:
            self.trait_element["kitten"].set_selected_list(list(traits))

        self.trait_element["adult"] = UIScrollingDropDown(
            pygame.Rect((110, 20), (140, 30)),
            dropdown_dimensions=(140, 198),
            item_list=self.adult_traits,
            parent_text="adult traits",
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["allow"],
            },
            manager=MANAGER,
        )
        traits = set(self.current_cat_dict["trait"]).intersection(self.adult_traits)
        if traits:
            self.trait_element["adult"].set_selected_list(list(traits))

        self.trait_element["include_info"] = UITextBoxTweaked(
            f"chosen allowed traits: {self.current_cat_dict['trait']}",
            ui_scale(pygame.Rect((10, 60), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["allow"],
            },
            allow_split_dashes=False,
        )
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.create_lock(
            name=f"{label}_trait",
            top_anchor=self.trait_element["allow"],
            left_anchor=self.trait_element["include_info"],
            y_offset=60,
        )
        self.trait_element["exclude_info"] = UITextBoxTweaked(
            f"chosen excluded traits: {self.current_cat_dict['not_trait']}",
            ui_scale(pygame.Rect((10, 10), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["include_info"],
            },
            allow_split_dashes=False,
        )
        self.create_lock(
            name=f"{label}_not_trait",
            top_anchor=self.trait_element["include_info"],
            left_anchor=self.trait_element["exclude_info"],
        )
        self.create_divider(self.trait_element["exclude_info"], "traits")

    def create_skill_editor(self, prev_element=None):
        self.skill_element["text"] = UITextBoxTweaked(
            "screens.event_edit.skill_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["rel_status"]
                if not prev_element
                else prev_element
            },
        )
        self.skill_element["paths"] = UIScrollingButtonList(
            pygame.Rect((30, 20), (140, 198)),
            item_list=[path for path in self.all_skills.keys()],
            button_dimensions=(140, 30),
            multiple_choice=False,
            container=self.editor_container,
            anchors={"top_target": self.skill_element["text"]},
            manager=MANAGER,
        )
        self.skill_element["allow"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((30, 20), (80, 30))),
            "allow",
            get_button_dict(ButtonStyles.MENU_LEFT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_left",
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["text"],
                "left_target": self.skill_element["paths"],
            },
        )
        # allow is picked by default, so this is initially disabled
        self.skill_element["allow"].disable()
        self.skill_element["exclude"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 20), (80, 30))),
            "exclude",
            get_button_dict(ButtonStyles.MENU_RIGHT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_right",
            container=self.editor_container,
            anchors={
                "left_target": self.skill_element["allow"],
                "top_target": self.skill_element["text"],
            },
        )
        self.skill_element["frame"] = UIModifiedImage(
            ui_scale(pygame.Rect((-20, 20), (254, 130))),
            get_box(BoxStyles.ROUNDED_BOX, (254, 130)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["allow"],
                "left_target": self.skill_element["paths"],
            },
        )
        self.skill_element["frame"].disable()
        self.skill_element["include_info"] = UITextBoxTweaked(
            f"chosen allowed skills: {self.current_cat_dict['skill']}",
            ui_scale(pygame.Rect((10, 10), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["paths"],
            },
            allow_split_dashes=False,
        )
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.create_lock(
            name=f"{label}_skill",
            top_anchor=self.skill_element["paths"],
            left_anchor=self.skill_element["include_info"],
        )
        self.skill_element["exclude_info"] = UITextBoxTweaked(
            f"chosen excluded skills: {self.current_cat_dict['not_skill']}",
            ui_scale(pygame.Rect((10, 10), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["include_info"],
            },
            allow_split_dashes=False,
        )
        self.create_lock(
            name=f"{label}_not_skill",
            top_anchor=self.skill_element["include_info"],
            left_anchor=self.skill_element["exclude_info"],
        )
        self.create_divider(self.skill_element["exclude_info"], "skills")

    def update_level_list(self):
        # kill existing buttons
        if self.level_element:
            for ele in self.level_element.values():
                ele.kill()

        # if no path is selected, don't make new buttons
        if not self.open_path:
            return

        # make new buttons
        level_list = self.all_skills[self.open_path]
        prev_element = None
        for level in range(len(level_list)):
            self.level_element[f"{level + 1}"] = UISurfaceImageButton(
                ui_scale(
                    pygame.Rect((-4, (28 if not prev_element else -2)), (230, 30))
                ),
                level_list[level],
                get_button_dict(ButtonStyles.DROPDOWN, (230, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "top_target": (
                        self.skill_element["allow"]
                        if not prev_element
                        else prev_element
                    ),
                    "left_target": self.skill_element["paths"],
                },
            )
            prev_element = self.level_element[f"{level + 1}"]

    def create_rel_status_editor(self):
        if self.rel_status_element:
            for ele in self.rel_status_element.values():
                ele.kill()
            self.rel_status_element.clear()

        # only the main cat has access to these tags
        if self.current_editor_tab == "main cat":
            self.rel_status_element["container"] = UICollapsibleContainer(
                ui_scale(pygame.Rect((0, 0), (440, 0))),
                title_text="<b>relationship_status:</b>",
                top_button_oriented_left=False,
                bottom_button=False,
                scrolling_container_to_reset=self.editor_container,
                manager=MANAGER,
                container=self.editor_container,
                title_object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
                anchors={"top_target": self.editor_element["age"]},
            )
            prev_element = None
            # CHECKBOXES
            # clear old elements
            if self.rel_status_checkbox:
                for info in self.rel_tag_list:
                    if (
                        info["tag"] in self.main_cat_info["rel_status"]
                        and not info["setting"]
                    ):
                        info["setting"] = True
                    if self.rel_status_checkbox.get(f"{info['tag']}_text"):
                        self.rel_status_checkbox[f"{info['tag']}_text"].kill()
                    if self.rel_status_checkbox.get(info["tag"]):
                        self.rel_status_checkbox[info["tag"]].kill()
            # make new ones!
            for info in self.rel_tag_list:
                self.rel_status_element[f"{info['tag']}_text"] = UITextBoxTweaked(
                    f"screens.event_edit.{info['tag']}",
                    ui_scale(
                        pygame.Rect((20, 40 if not prev_element else 10), (350, -1))
                    ),
                    object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
                    line_spacing=1,
                    manager=MANAGER,
                    container=self.rel_status_element["container"],
                    anchors={
                        "top_target": prev_element,
                    }
                    if prev_element
                    else None,
                )

                self.rel_status_checkbox[info["tag"]] = UICheckbox(
                    position=(370, 40 if not prev_element else 10),
                    container=self.rel_status_element["container"],
                    manager=MANAGER,
                    check=info["setting"],
                    anchors={"top_target": prev_element} if prev_element else None,
                )

                prev_element = self.rel_status_element[f"{info['tag']}_text"]

        # VALUE TAGS
        prev_element = (
            self.rel_status_element["container"]
            if self.rel_status_element.get("container")
            else self.editor_element["age"]
        )
        for value in self.rel_value_types.keys():
            self.rel_status_element[f"{value}_text"] = UITextBoxTweaked(
                f"{value} levels allowed:",
                ui_scale(pygame.Rect((40, 10), (-1, -1))),
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
                line_spacing=1,
                manager=MANAGER,
                container=self.editor_container,
                anchors={
                    "top_target": prev_element,
                },
            )
            self.rel_status_element[f"{value}_dropdown"] = UIScrollingDropDown(
                pygame.Rect((120, 10 if prev_element else 0), (140, 30)),
                manager=MANAGER,
                container=self.editor_container,
                parent_text=f"{value} levels",
                item_list=self.rel_value_types[value],
                dropdown_dimensions=(140, 198),
                anchors={
                    "top_target": prev_element,
                },
                starting_height=1,
                starting_selection=[
                    l
                    for l in self.current_cat_dict["rel_status"]
                    if l in self.rel_value_types[value]
                    or f"{l}_only" in self.rel_value_types[value]
                ],
            )

            self.rel_status_element[f"{value}_checkbox"] = UICheckbox(
                (-5, 10),
                container=self.editor_container,
                manager=MANAGER,
                tool_tip_text="Do not allow higher levels than what is selected.",
                anchors={
                    "top_target": prev_element,
                    "left_target": self.rel_status_element[f"{value}_dropdown"],
                },
            )

            for level in self.rel_value_types[value]:
                if f"{level}_only" in self.current_cat_dict["rel_status"]:
                    self.rel_status_element[f"{value}_checkbox"].check()
                    break

            prev_element = self.rel_status_element[f"{value}_text"]

        self.rel_status_element["display"] = UITextBoxTweaked(
            f"chosen relationship_status: {self.current_cat_dict['rel_status']}",
            ui_scale(pygame.Rect((10, 10), (380, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={"top_target": prev_element},
        )
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.create_lock(
            name=f"{label}_rel_status",
            top_anchor=prev_element,
            left_anchor=self.rel_status_element["display"],
        )
        if self.rel_status_element.get("container"):
            self.rel_status_element["container"].close()
        self.create_divider(self.rel_status_element["display"], "rel_status")

    def create_age_editor(self):
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.age_element = EditorDropDownSelection(
            position=(0, 10),
            anchors={"top_target": self.editor_element["rank"]},
            container=self.editor_container,
            manager=MANAGER,
            description="screens.event_edit.age_info",
            item_list=self.all_ages,
            dropdown_parent_text="ages",
            display_text="chosen age: ",
            starting_selection=self.current_cat_dict["age"],
            multiple_choice=True,
            lock_name=f"{label}_age",
            lock=True,
        )
        if self.param_locks.get(f"{label}_age"):
            self.age_element.lock.locked = True

        self.create_divider(self.age_element.bottom_element, "age")

    def create_rank_editor(self, prev_element=None):
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.rank_element = EditorDropDownSelection(
            position=(0, 10),
            anchors={
                "top_target": self.editor_element["dies"]
                if not prev_element
                else prev_element
            },
            container=self.editor_container,
            manager=MANAGER,
            description="screens.event_edit.rank_info",
            item_list=self.all_ranks,
            dropdown_parent_text="ranks",
            display_text="chosen rank: ",
            starting_selection=self.current_cat_dict["rank"],
            multiple_choice=True,
            lock_name=f"{label}_rank",
            lock=True,
        )
        if self.param_locks.get(f"{label}_rank"):
            self.rank_element.lock.locked = True

        self.create_divider(self.rank_element.bottom_element, "rank")

    def create_dies_editor(self, editor):
        self.death_element["checkbox"] = UICheckbox(
            position=(7, 7),
            container=self.editor_container,
            manager=MANAGER,
            anchors={"top_target": editor["intro"]},
            check=self.current_cat_dict["dies"],
        )
        # this checks if death is requried and locks out user input
        if (
            "death" in self.settings_tab.type_info
            and self.current_editor_tab == "main cat"
        ):
            self.death_element["checkbox"].check()
            self.death_element["checkbox"].disable()
            self.current_cat_dict["dies"] = True

        # this just checks if the cat's dict says they should die
        if self.current_cat_dict["dies"] and not self.death_element["checkbox"].checked:
            self.death_element["checkbox"].check()

        self.death_element["text"] = UITextBoxTweaked(
            "screens.event_edit.death_info",
            ui_scale(pygame.Rect((40, 6), (-1, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={"top_target": editor["intro"]},
        )

        self.death_element["display"] = UITextBoxTweaked(
            f"dies: {self.current_cat_dict['dies']}",
            ui_scale(pygame.Rect((0, 6), (-1, -1))),
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_10_10"),
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.death_element["text"],
            },
        )
        label = "main" if self.current_cat_dict == self.main_cat_info else "random"
        self.create_lock(
            name=f"{label}_dies",
            top_anchor=self.death_element["text"],
            left_anchor=self.death_element["display"],
            x_offset=320,
        )
        self.create_divider(self.death_element["display"], "dies")
