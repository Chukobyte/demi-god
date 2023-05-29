from crescent_api import *

from src.characters.player import Player
from src.level_area_manager import LevelAreaManager
from src.level_state import LevelState
from src.utils.task import *


class GameTimer:
    def __init__(self, time_label: TextLabel):
        self.time_label = time_label
        self._time = 0.0

    def _get_formatted_time(self) -> str:
        time_seconds = int(self._time)
        if time_seconds < 10:
            return f"00:0{time_seconds}"
        elif time_seconds < 60:
            return f"00:{time_seconds}"
        else:
            time_minutes = int(time_seconds / 60)
            if time_minutes < 10:
                minutes_string = f"0{time_minutes}"
            else:
                minutes_string = f"{time_minutes}"
            left_over_seconds = int(time_seconds - time_minutes * 60)
            if left_over_seconds < 10:
                seconds_string = f"0{left_over_seconds}"
            else:
                seconds_string = f"{left_over_seconds}"
            return f"{minutes_string}:{seconds_string}"

    def update(self) -> None:
        delta_time = World.get_delta_time()
        prev_time = self._time
        self._time += delta_time
        if prev_time != self._time:
            self.time_label.text = self._get_formatted_time()


class GameMaster:
    # Manages game state such as enemy spawning
    def __init__(self, main_node):
        self.main = main_node
        self.player: Optional[Player] = None
        self.main_task = Task(coroutine=self._update_task())
        self.bridge_transition_task: Optional[Task] = None

    def update(self) -> None:
        self.main_task.resume()

    # --- TASKS --- #
    async def _update_task(self):
        player_start_pos = Vector2(20, 78)
        level_area_manager = LevelAreaManager()
        game_timer = GameTimer(SceneTree.get_root().get_child("TimeLabel"))
        try:
            # Call update once to set initial area up
            level_area_manager.update()

            # TODO: put in main.py
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))

            # Shoot down player beam first
            await Task(coroutine=level_area_manager.beam_player_down(player_start_pos))

            main_theme_audio_source = AudioManager.get_audio_source(
                "assets/audio/music/main_theme.wav"
            )
            AudioManager.play_sound(source=main_theme_audio_source, loops=True)

            player_scene = SceneUtil.load_scene("scenes/characters/player.cscn")
            self.player: Player = player_scene.create_instance()
            self.player.position = player_start_pos
            self.main.add_child(self.player)

            while True:
                level_area_manager.update()
                game_timer.update()
                await co_suspend()
        except GeneratorExit:
            pass
