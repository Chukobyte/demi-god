from crescent_api import *

from src.level_state import LevelState
from src.option_box_manager import OptionBoxManager
from src.utils.task import Task, co_suspend


class EndGameScreen(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.update_task = Task(coroutine=self._update_task())
        self.game_time_label: Optional[TextLabel] = None
        self.confirmed_option: Optional[str] = None
        self.can_update_options = False
        self.option_box_manager: Optional[OptionBoxManager] = None

    def _start(self) -> None:
        self.game_time_label: TextLabel = self.get_child("GameTimeLabel")
        level_state = LevelState()
        self.game_time_label.text = (
            f"Game Time: {level_state.game_timer.get_formatted_time()}"
        )
        option_box_text_label: TextLabel = self.get_child("OptionsTextLabel")
        option_arrow_top_sprite: Sprite = self.get_child("OptionArrowTop")
        option_arrow_bottom_sprite: Sprite = self.get_child("OptionArrowBot")
        self.option_box_manager = OptionBoxManager(
            option_box_text_label,
            option_arrow_bottom_sprite,
            option_arrow_top_sprite,
            ["Retry", "Title", "Exit"],
        )

    def _end(self) -> None:
        LevelState.reset_instance()
        level_state = LevelState()
        level_state.screen_shader_instance = ShaderUtil.get_current_screen_shader()

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("exit"):
            Engine.exit()

        if self.can_update_options:
            self.option_box_manager.process_inputs()
            if Input.is_action_just_pressed("start"):
                self.confirmed_option = self.option_box_manager.get_selected_option()
                self.option_box_manager.is_enabled = False

    def _fixed_update(self, delta_time: float) -> None:
        self.update_task.resume()
        self.option_box_manager.update_tasks()

    # --- TASKS --- #
    async def _update_task(self):
        try:
            # Fade in
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))
            self.can_update_options = True
            # Wait for request to go to the title screen
            while not self.confirmed_option:
                await co_suspend()
            confirmed_option = self.confirmed_option
            # Fade out
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=True))
            if confirmed_option == "Retry":
                SceneTree.change_scene("scenes/main.cscn")
            elif confirmed_option == "Title":
                SceneTree.change_scene("scenes/title_screen.cscn")
            elif confirmed_option == "Exit":
                Engine.exit()
        except GeneratorExit:
            pass
