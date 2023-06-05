from crescent_api import Vector2

from src.characters.enemy import Enemy
from src.level_state import LevelState
from src.utils.game_math import Easer, Ease
from src.utils.task import *
from src.utils.timer import Timer


class EnemyBoss(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(8)
        self.move_dir = Vector2.RIGHT()
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.do_entrance_stuff = True

    def _start(self) -> None:
        super()._start()
        self.anim_sprite.flip_h = True
        if self.do_entrance_stuff:
            self.position += Vector2(0, -101)
        else:
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

            if self.do_entrance_stuff:
                landing_pos = self.position + Vector2(0, 100)
                await Task(coroutine=self._entrance_task(landing_pos))
            level_state = LevelState()
            level_state.is_paused_from_boss = False

            move_speed = 30
            _update_move_dir()
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position += self.move_dir * Vector2(
                    move_speed * delta_time, move_speed * delta_time
                )
                if self.position.distance_to(player.position) > 60:
                    _update_move_dir()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _entrance_task(self, landing_pos: Vector2) -> None:
        try:
            # Fall from the sky and land
            landing_time = 5.0
            landing_timer = Timer(landing_time)
            enemy_landing_easer = Easer(
                self.position,
                landing_pos,
                landing_timer.time,
                Ease.Cubic.ease_out_vec2,
            )
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                landing_timer.tick(delta_time)
                if landing_timer.has_stopped():
                    self.position = landing_pos
                    break
                else:
                    self.position = enemy_landing_easer.ease(delta_time)
                await co_suspend()
            # TODO: Do anything else after landing, like an animation
            await co_suspend()
            await co_suspend()
            await co_suspend()
        except GeneratorExit:
            pass
