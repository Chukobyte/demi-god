from crescent_api import Vector2

from src.characters.enemy import Enemy
from src.utils.task import *
from src.utils.timer import Timer


class EnemyRabbit(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(1)
        self.can_attach_to_player = True
        self.physics_update_task = Task(coroutine=self._physics_update_task())

    def destroy_from_shake(self) -> None:
        if not self.is_destroyed:
            self.is_destroyed = True
            self.broadcast_event("destroyed", self)
            self.destroyed_task = Task(coroutine=self._destroy_from_shake_task())

    # --- TASKS --- #
    async def _destroy_from_shake_task(self) -> None:
        try:
            # fly_speed = 60
            # if self.anim_sprite.flip_h:
            #     fly_dir = Vector2.RIGHT
            # else:
            #     fly_dir = Vector2.LEFT
            # fly_dir.y = -1
            fly_timer = Timer(5.0)
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                fly_timer.tick(delta_time)
                if fly_timer.has_stopped():
                    break
                # self.position += fly_dir * Vector2(
                #     fly_speed * delta_time, fly_speed * delta_time
                # )
                await co_suspend()
            self.queue_deletion()
        except GeneratorExit:
            pass

    async def _physics_update_task(self) -> None:
        try:
            player = self._find_player()
            move_speed = 30
            if player.position.x > self.position.x:
                move_dir = Vector2.RIGHT
            else:
                self.anim_sprite.flip_h = True
                move_dir = Vector2.LEFT
            while True:
                if not self.is_attached_to_player:
                    delta_time = self.get_full_time_dilation_with_physics_delta()
                    self.position += move_dir * Vector2(
                        move_speed * delta_time, move_speed * delta_time
                    )
                await co_suspend()
        except GeneratorExit:
            pass
