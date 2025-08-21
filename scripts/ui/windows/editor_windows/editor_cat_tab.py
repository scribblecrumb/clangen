import math
from fractions import Fraction

import i18n
import pygame
import pygame_gui.elements

from scripts.cat.cats import Cat
from scripts.clan_package.settings import (
    get_clan_setting,
    switch_clan_setting,
)
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import (
    UISurfaceImageButton,
    UIImageButton,
    UICheckbox,
    UITextBoxTweaked,
    UICatListDisplay,
    UIModifiedScrollingContainer,
)
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.icon import Icon
from scripts.ui.windows.base_window import GameWindow
from scripts.utility import (
    ui_scale,
    ui_scale_offset,
    ui_scale_value,
    get_text_box_theme,
)


class EditorCatTab(GameWindow):
    def __init__(
        self,
        tag_info: list,
        basic_tag_list: list,
        type_info: list,
        tag_element: dict,
        editor_container,
    ):
        super().__init__(
            ui_scale(pygame.Rect((175, 100), (450, 500))),
            window_display_title="Editor Cats",
        )





    def process_event(self, event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_PRESSED:


        return super().process_event(event)
