from typing import List, Optional

from crescent_api import TextLabel, Input, Vector2


class OptionInputsResponse:
    def __init__(self, selected_option: str, confirmed: bool):
        self.selected_option = selected_option
        self.has_been_confirmed = confirmed


class OptionBoxManager:
    def __init__(self, option_text_label: TextLabel, options: List[str]):
        self.option_text_label = option_text_label
        self.options = options
        self._current_index = 0
        self._initial_text_pos = self.option_text_label.position

    def get_selected_option(self) -> str:
        return self.options[self._current_index]

    def process_inputs(self) -> Optional[OptionInputsResponse]:
        # Confirm
        if Input.is_action_just_pressed("start"):
            return OptionInputsResponse(
                selected_option=self.get_selected_option(), confirmed=True
            )
        # Up
        if Input.is_action_just_pressed("jump"):
            self._current_index -= 1
            if self._current_index < 0:
                self._current_index = len(self.options) - 1
            selected_option = self.get_selected_option()
            self._update_text_label(selected_option)
            return OptionInputsResponse(
                selected_option=selected_option, confirmed=False
            )
        # Down
        elif Input.is_action_just_pressed("crouch"):
            self._current_index += 1
            if self._current_index >= len(self.options):
                self._current_index = 0
            selected_option = self.get_selected_option()
            self._update_text_label(selected_option)
            return OptionInputsResponse(
                selected_option=selected_option, confirmed=False
            )
        return None

    def _update_text_label(self, text: str) -> None:
        # Need to update positions as we don't have proper text label functionality yet...
        if len(text) == 4:
            self.option_text_label.position = self._initial_text_pos + Vector2(4, 0)
        else:
            self.option_text_label.position = self._initial_text_pos
        self.option_text_label.text = text
