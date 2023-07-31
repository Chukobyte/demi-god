from typing import Optional, List, Type

from crescent_api import Color, TextLabel, SceneTree, ColorRect

from src.items import Item


class PlayerItemHandler:
    def __init__(self):
        self.window_bg: ColorRect = (
            SceneTree.get_root().get_child("BottomUI").get_child("TextWindow")
        )
        self.text_label_top: TextLabel = self.window_bg.get_child("WindowTextTop")
        self.text_label_bottom: TextLabel = self.window_bg.get_child("WindowTextBot")
        window_color = self.window_bg.color
        self.show_color = Color(window_color.r, window_color.g, window_color.b)
        self.hide_color = window_color
        self.item_shown: Optional[Item] = None
        self.held_unique_items: List[Type] = []

    def show_description(self, item: Item) -> None:
        if not self.item_shown and not item.active:
            item.set_item_highlighted(is_highlighted=True)
            top_description = item.description_top
            bottom_description = item.description_bottom
            if top_description or bottom_description:
                self.window_bg.color = self.show_color
                self.text_label_top.text = item.description_top
                self.text_label_bottom.text = item.description_bottom
            self.item_shown = item

    def hide_description(self) -> None:
        if self.item_shown:
            self.item_shown.set_item_highlighted(is_highlighted=False)
            self.window_bg.color = self.hide_color
            self.text_label_top.text = ""
            self.text_label_bottom.text = ""
            self.item_shown = None

    def get_hovered_item(self) -> Optional[Item]:
        return self.item_shown
