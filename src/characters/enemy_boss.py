from crescent_api import Vector2, AnimatedSprite

from src.utils.task import *
from src.characters.enemy import Enemy


class EnemyBoss(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(4)
        self.move_dir = Vector2.RIGHT()
        self.physics_update_task = Task(coroutine=self._physics_update_task())

    def _start(self) -> None:
        super()._start()
        self.position += Vector2(0, -1)

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        def _update_move_dir() -> None:
            if player.position.x > self.position.x:
                self.anim_sprite.flip_h = False
                self.move_dir = Vector2.RIGHT()
            else:
                self.anim_sprite.flip_h = True
                self.move_dir = Vector2.LEFT()

        try:
            player = self._find_player()
            move_speed = 30
            _update_move_dir()
            while True:
                if self._is_outside_of_level_boundary():
                    self.queue_deletion()
                    await co_return()
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position += self.move_dir * Vector2(
                    move_speed * delta_time, move_speed * delta_time
                )
                if self.position.distance_to(player.position) > 60:
                    _update_move_dir()
                await co_suspend()
        except GeneratorExit:
            pass
