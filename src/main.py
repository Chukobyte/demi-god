from crescent_api import *

from src.game_master import GameMaster
from src.level_state import LevelState


class Main(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id=entity_id)
        self.game_master = GameMaster(self)
        self.main_theme_audio_source: Optional[AudioSource] = None

    def _start(self) -> None:
        # Set up stuff based on level boundaries
        level_state = LevelState()
        bg_color_rect: ColorRect = self.get_child("ColorRect")
        bg_color_rect.size = Size2D(level_state.boundary.w * 2.0, bg_color_rect.size.h)
        bridge_ground: Sprite = self.get_child("BridgeGround")
        bridge_ground_draw_source = bridge_ground.draw_source
        bridge_ground_draw_source.w = level_state.boundary.w * 2.0
        bridge_ground.draw_source = bridge_ground_draw_source
        buildings: Sprite = self.get_child("Parallax").get_child("Buildings")
        buildings_draw_source = buildings.draw_source
        buildings_draw_source.w = level_state.boundary.w * 2.0
        buildings.draw_source = buildings_draw_source

    def _end(self) -> None:
        self.main_theme_audio_source = AudioManager.get_audio_source(
            "assets/audio/music/main_theme.wav"
        )
        AudioManager.stop_sound(source=self.main_theme_audio_source)

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("exit"):
            Engine.exit()

    def _fixed_update(self, delta_time: float) -> None:
        self.game_master.update()
