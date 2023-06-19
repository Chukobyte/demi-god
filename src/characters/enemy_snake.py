from crescent_api import Vector2, MinMax

from src.characters.enemy import Enemy
from src.utils.task import *
from src.utils.timer import Timer


class EnemySnake(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(1)
        self.destroy_on_touch = True
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.split_range = MinMax(0.9, 0.9)
        self.split_amount = 0.02

    def _get_move_dir(self, player) -> Vector2:
        if player.position.x > self.position.x:
            return Vector2.RIGHT
        else:
            return Vector2.LEFT

    def destroy_from_contact(self) -> None:
        # TODO: Fix rotation position with camera in engine.
        if not self.is_destroyed:
            self.is_destroyed = True
            self.broadcast_event("destroyed", self)
            self.anim_sprite.play("death")
            self.destroyed_task = Task(coroutine=self._destroy_from_contact_task())

    # --- TASKS --- #
    async def _destroy_from_contact_task(self) -> None:
        try:
            fly_speed = 40
            if self.anim_sprite.flip_h:
                fly_dir = Vector2(1, -1)
            else:
                fly_dir = Vector2(-1, -1)
            # Ascend
            ascend_timer = Timer(0.25)
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                ascend_timer.tick(delta_time)
                if ascend_timer.has_stopped():
                    break
                self.position += fly_dir * Vector2(
                    fly_speed * delta_time, fly_speed * delta_time
                )
                await co_suspend()
            # Descend
            fly_speed = 30
            fly_dir = Vector2(0, 1)
            descend_timer = Timer(4.5)
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                descend_timer.tick(delta_time)
                if descend_timer.has_stopped():
                    break
                self.position += fly_dir * Vector2(
                    fly_speed * delta_time, fly_speed * delta_time
                )
                await co_suspend()
            self.queue_deletion()
        except GeneratorExit:
            pass

    async def _physics_update_task(self) -> None:
        try:
            player = self._find_player()
            move_speed = 30
            has_passed_player = False
            move_dir = self._get_move_dir(player)
            if move_dir == Vector2.LEFT:
                self.anim_sprite.flip_h = True
            while True:
                if has_passed_player and self._is_outside_of_camera_viewport():
                    self.destroy()
                    await co_return()
                else:
                    dir_to_player = self._get_move_dir(player)
                    if move_dir != dir_to_player:
                        has_passed_player = True
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position += move_dir * Vector2(
                    move_speed * delta_time, move_speed * delta_time
                )
                await co_suspend()
        except GeneratorExit:
            pass
