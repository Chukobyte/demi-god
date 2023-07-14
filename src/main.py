from crescent_api import *

from src.game_master import GameMaster
from src.utils.task import Task, co_suspend


class Main(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id=entity_id)
        self.game_master = GameMaster(self)
        self.main_theme_audio_source: Optional[AudioSource] = None
        self.ground_scroll_task: Optional[Task] = None

    def _start(self) -> None:
        max_game_width = 9999.0
        bg_color_rect: ColorRect = self.get_child("BGColorRect")
        bg_color_rect.size = Size2D(max_game_width, bg_color_rect.size.h)
        # Bridge Ground
        bridge_ground: Sprite = self.get_child("BridgeGround")
        bridge_ground_draw_source = bridge_ground.draw_source
        bridge_ground_draw_source.w = max_game_width
        bridge_ground.draw_source = bridge_ground_draw_source
        bridge_ground_bottom_railings: Sprite = self.get_child("BottomRailings")
        bridge_ground_bottom_railings.draw_source = bridge_ground_draw_source
        # Buildings Background
        # buildings: AnimatedSprite = self.get_child("Parallax").get_child("Buildings")
        # buildings_draw_source = buildings.draw_source
        # buildings_draw_source.w = max_game_width
        # buildings.draw_source = buildings_draw_source
        buildings_draw_source = Rect2(0.0, 0.0, 320.0, 144.0)
        buildings_draw_source.w = max_game_width
        # Ground
        bg_ground: Sprite = self.get_child("ParallaxBack").get_child("Ground")
        bg_ground.draw_source = buildings_draw_source
        self.ground_scroll_task = Task(coroutine=self._ground_scroll_task(bg_ground))
        # Back buildings
        back_buildings: Sprite = self.get_child("ParallaxBack").get_child("Buildings")
        back_buildings.draw_source = buildings_draw_source

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("exit"):
            Engine.exit()

    def _fixed_update(self, delta_time: float) -> None:
        self.game_master.update()
        if self.ground_scroll_task:
            self.ground_scroll_task.resume()

    async def _ground_scroll_task(self, bg_ground: Sprite):
        try:
            move_speed = 2
            while True:
                delta_time = World.get_time_dilation() * World.get_delta_time()
                new_pos = bg_ground.position
                new_pos += Vector2.RIGHT * Vector2(delta_time * move_speed, 0)
                # Prevent from running out of image
                if new_pos.x >= 0.0:
                    new_pos.x = -6400.0
                bg_ground.position = new_pos

                await co_suspend()
        except GeneratorExit:
            pass
