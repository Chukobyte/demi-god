import math
import random

from crescent_api import Vector2, Node2D

from src.characters.enemy import Enemy
from src.level_state import LevelState
from src.utils.task import *
from src.utils.timer import Timer


class EnemyCrowState:
    HOVERING = "hovering"
    SWOOPING = "swooping"
    BACK_TO_HOVER = "back_to_hover"


HOVER_HEIGHT = 48


class EnemyCrow(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(1)
        self.move_speed = 40
        self.state = EnemyCrowState.HOVERING
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.player: Optional[Node2D] = None
        self.level_state = LevelState()

    def _start(self) -> None:
        super()._start()
        self.player = self._find_player()
        # Start at a certain height above the floor
        self.position -= Vector2(0, HOVER_HEIGHT)

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        try:
            prev_state = None
            state_task: Optional[Task] = None
            while True:
                # Update state task if changed
                if self.state != prev_state:
                    if state_task:
                        state_task.close()
                    if self.state == EnemyCrowState.HOVERING:
                        state_task = Task(coroutine=self._hovering_state_task())
                    elif self.state == EnemyCrowState.SWOOPING:
                        state_task = Task(coroutine=self._swooping_state_task())
                    elif self.state == EnemyCrowState.BACK_TO_HOVER:
                        state_task = Task(coroutine=self._back_to_hover_state_task())
                    else:
                        print(f"ERROR: Invalid crow state {self.state}!")
                prev_state = self.state
                state_task.resume()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _hovering_state_task(self) -> None:
        try:
            self.anim_sprite.play(name="fly")
            swoop_timer = Timer(random.uniform(5.0, 8.0))
            player_dir_update_timer = Timer(random.uniform(2.0, 4.0))
            player_dir = self.position.direction_to(self.player.position)
            while True:
                if self._is_outside_of_level_boundary():
                    self.queue_deletion()
                    await co_return()

                delta_time = self.get_full_time_dilation_with_physics_delta()
                move_vector = Vector2(
                    self.move_speed * delta_time, self.move_speed * delta_time
                )
                distance_from_player = self.position.distance_to(self.player.position)
                swoop_timer.tick(delta_time)
                if swoop_timer.time_remaining <= 0.0 and distance_from_player < 80:
                    self.state = EnemyCrowState.SWOOPING
                    await co_return()
                player_dir_update_timer.tick(delta_time)
                if (
                    player_dir_update_timer.time_remaining <= 0.0
                    or distance_from_player > 90
                ):
                    player_dir = self.position.direction_to(self.player.position)
                    player_dir_update_timer.time = random.uniform(2.0, 4.0)
                    player_dir_update_timer.reset()
                if player_dir.x > 0:
                    self.anim_sprite.flip_h = False
                else:
                    self.anim_sprite.flip_h = True
                dir_sign_x = math.copysign(1, player_dir.x)
                self.position += Vector2(dir_sign_x, 0.0) * move_vector
                await co_suspend()
        except GeneratorExit:
            pass

    async def _swooping_state_task(self) -> None:
        try:
            self.anim_sprite.stop()
            self.anim_sprite.set_current_animation_frame(frame=0)
            swoop_speed = self.move_speed + 10
            player_dir = self.position.direction_to(self.player.position)
            if player_dir.x > 0:
                self.anim_sprite.flip_h = False
            else:
                self.anim_sprite.flip_h = True
            while True:
                if self._is_outside_of_level_boundary(padding=Vector2(64, 0)):
                    self.state = EnemyCrowState.BACK_TO_HOVER
                    await co_return()

                delta_time = self.get_full_time_dilation_with_physics_delta()
                move_vector = Vector2(
                    swoop_speed * delta_time, swoop_speed * delta_time
                )
                self.position += player_dir * move_vector
                await co_suspend()
        except GeneratorExit:
            pass

    async def _back_to_hover_state_task(self) -> None:
        try:
            self.anim_sprite.play(name="fly")
            current_pos = self.position
            hover_pos = Vector2(current_pos.x, self.level_state.floor_y - HOVER_HEIGHT)
            move_dir = current_pos.direction_to(hover_pos)
            if move_dir.x > 0:
                self.anim_sprite.flip_h = False
            else:
                self.anim_sprite.flip_h = True
            while True:
                distance_from_hover_pos = self.position.distance_to(hover_pos)
                if distance_from_hover_pos <= 2:
                    self.position = hover_pos
                    self.state = EnemyCrowState.HOVERING
                    await co_return()

                delta_time = self.get_full_time_dilation_with_physics_delta()
                move_vector = Vector2(
                    self.move_speed * delta_time, self.move_speed * delta_time
                )
                self.position += move_dir * move_vector
                await co_suspend()
        except GeneratorExit:
            pass
