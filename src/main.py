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
        bg_ground: Sprite = self.get_child("ParallaxBack").get_child("Ground")
        self.ground_scroll_task = Task(coroutine=self._ground_scroll_task(bg_ground))

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
