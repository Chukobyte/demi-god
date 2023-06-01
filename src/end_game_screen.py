from crescent_api import *

from src.level_state import LevelState
from src.utils.task import Task, co_suspend


class EndGameScreen(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.update_task = Task(coroutine=self._update_task())
        self.game_time_label: Optional[TextLabel] = None
        self.should_go_to_title_screen = False

    def _start(self) -> None:
        self.game_time_label: TextLabel = self.get_child("GameTimeLabel")
        level_state = LevelState()
        self.game_time_label.text = (
            f"Game Time: {level_state.game_timer.get_formatted_time()}"
        )

    def _end(self) -> None:
        LevelState.reset_instance()

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("exit"):
            Engine.exit()

        if Input.is_action_just_pressed("start"):
            self.should_go_to_title_screen = True

    def _fixed_update(self, delta_time: float) -> None:
        self.update_task.resume()

    # --- TASKS --- #
    async def _update_task(self):
        try:
            # Fade in
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))
            # Wait for request to go to the title screen
            while not self.should_go_to_title_screen:
                await co_suspend()
            # Fade out
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=True))
            SceneTree.change_scene("scenes/title_screen.cscn")
        except GeneratorExit:
            pass
