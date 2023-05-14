from crescent_api import *

from src.game_master import GameMaster


class Main(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id=entity_id)
        self.game_master = GameMaster(self)
        self.main_theme_audio_source: Optional[AudioSource] = None

    def _start(self) -> None:
        max_game_width = 9999.0
        bg_color_rect: ColorRect = self.get_child("ColorRect")
        bg_color_rect.size = Size2D(max_game_width, bg_color_rect.size.h)
        bridge_ground: Sprite = self.get_child("BridgeGround")
        bridge_ground_draw_source = bridge_ground.draw_source
        bridge_ground_draw_source.w = max_game_width
        bridge_ground.draw_source = bridge_ground_draw_source
        buildings: Sprite = self.get_child("Parallax").get_child("Buildings")
        buildings_draw_source = buildings.draw_source
        buildings_draw_source.w = max_game_width
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
