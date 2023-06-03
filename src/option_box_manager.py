from typing import List, Optional

from crescent_api import TextLabel, Input, Vector2, Sprite, Color

from src.utils.task import Task, co_wait_seconds, co_suspend


class OptionInputsResponse:
    def __init__(self, selected_option: str, confirmed: bool):
        self.selected_option = selected_option
        self.has_been_confirmed = confirmed


class OptionBoxManager:
    def __init__(
        self,
        option_text_label: TextLabel,
        arrow_bottom: Sprite,
        arrow_top: Sprite,
        options: List[str],
    ):
        self.option_text_label = option_text_label
        self.arrow_bottom = arrow_bottom
        self.arrow_top = arrow_top
        self.options = options
        self.is_enabled = True
        self._current_index = 0
        self._initial_text_pos = self.option_text_label.position
        self._normal_arrow_color = Color(240, 247, 243)
        self._flicker_arrow_color = Color(80, 80, 80)
        self._flicker_task: Optional[Task] = None

    def get_selected_option(self) -> str:
        if not self.is_enabled:
            return ""
        return self.options[self._current_index]

    def process_inputs(self) -> Optional[OptionInputsResponse]:
        if not self.is_enabled:
            return None
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
            self._flicker_task = Task(
                coroutine=self._flicker_arrow_task(self.arrow_top)
            )
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
            self._flicker_task = Task(
                coroutine=self._flicker_arrow_task(self.arrow_bottom)
            )
            return OptionInputsResponse(
                selected_option=selected_option, confirmed=False
            )
        return None

    def update_tasks(self) -> None:
        if self._flicker_task:
            self._flicker_task.resume()

    def _update_text_label(self, text: str) -> None:
        # Need to update positions as we don't have proper text label functionality yet...
        if len(text) == 4:
            self.option_text_label.position = self._initial_text_pos + Vector2(4, 0)
        else:
            self.option_text_label.position = self._initial_text_pos
        self.option_text_label.text = text

    # --- TASKS --- #
    async def _flicker_arrow_task(self, arrow: Sprite):
        has_finished = False
        try:
            arrow.modulate = self._flicker_arrow_color
            await co_suspend()
            arrow.modulate = self._normal_arrow_color
        except GeneratorExit:
            if not has_finished:
                arrow.modulate = self._normal_arrow_color
