from crescent_api import *

from src.characters.player import Player
from src.level_area_manager import LevelAreaManager
from src.level_state import LevelState
from src.utils.task import *


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
                await co_suspend()
        except GeneratorExit:
            pass
