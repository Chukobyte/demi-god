from typing import List, Optional

from crescent_api import *

from src.characters.enemy_definitions import EnemyDefinition
from src.characters.wandering_soul import WanderingSoul
from src.environment.bridge_gate import BridgeGate
from src.level_state import LevelState
from src.utils.game_math import Easer, Ease
from src.utils.task import co_suspend, co_wait_seconds, Task
from src.utils.timer import Timer


class LevelAreaType:
    NORMAL = "normal"
    POWER_UP = "power_up"
    BOSS = "boss"


class LevelArea:
    def __init__(
        self, area_type: str, width: int, enemy_defs: List[EnemyDefinition] = None
    ):
        self.area_type = area_type
        self.width = width
        if not enemy_defs:
            enemy_defs = []
        self.enemy_defs = enemy_defs


class LevelAreaDefinitions:
    DEF_MAP = {
        1: LevelArea(
            area_type=LevelAreaType.NORMAL,
            width=448,
            enemy_defs=[EnemyDefinition.RABBIT()],
        ),
        2: LevelArea(area_type=LevelAreaType.POWER_UP, width=160),
    }

    @staticmethod
    def get_def(area_num: int) -> Optional[LevelArea]:
        return LevelAreaDefinitions.DEF_MAP.get(area_num, None)


class LevelAreaManager:
    def setup_level_area(self, area: LevelArea) -> None:
        level_state = LevelState()
        level_state.boundary.w += area.width
        level_state.boundary.x = level_state.boundary.w - area.width
        Camera2D.set_boundary(level_state.boundary)

    def queue_next_area_transition(self) -> None:
        level_state = LevelState()
        level_state.is_gate_transition_queued = True
        level_state.is_currently_transitioning_within_level = True

    async def manage_level_areas(self):
        try:
            level_state = LevelState()
            manage_bridge_transition_task = Optional[Task]
            while True:
                # Need to handle waves for an area

                # Manage bridge transition
                if level_state.is_gate_transition_queued:
                    level_state.is_gate_transition_queued = False
                    if manage_bridge_transition_task:
                        manage_bridge_transition_task.close()
                    manage_bridge_transition_task = Task(
                        coroutine=self._manage_bridge_transition_task()
                    )
                if manage_bridge_transition_task:
                    manage_bridge_transition_task.resume()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _manage_bridge_transition_task(self):
        try:
            level_state = LevelState()
            prev_player_time_dilation = self.player.time_dilation
            self.player.time_dilation = 0.0
            for cloud in self.spawned_clouds:
                cloud.time_dilation = 0.0
            level_state.boundary.w += 160
            Camera2D.unfollow_node(self.player)
            Camera2D.set_boundary(level_state.boundary)
            transition_timer = Timer(5.0)
            initial_camera_pos = Camera2D.get_position()
            dest_camera_pos = Vector2(
                level_state.boundary.w - 160, initial_camera_pos.y
            )
            camera_pos_easer = Easer(
                initial_camera_pos,
                dest_camera_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            initial_player_pos = self.player.position
            player_dest_pos = initial_player_pos + Vector2(30, 0)
            player_pos_easer = Easer(
                initial_player_pos,
                player_dest_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            await co_wait_seconds(1.0)
            self.player.time_dilation = prev_player_time_dilation
            self.player.play_animation("walk")
            for cloud in self.spawned_clouds:
                cloud.time_dilation = 1.0

            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                transition_timer.tick(delta_time)
                if transition_timer.time_remaining <= 0.0:
                    Camera2D.set_position(dest_camera_pos)
                    self.player.position = player_dest_pos
                    break
                else:
                    new_camera_pos = camera_pos_easer.ease(delta_time)
                    Camera2D.set_position(new_camera_pos)
                    new_player_pos = player_pos_easer.ease(delta_time)
                    self.player.position = new_player_pos
                await co_suspend()
            level_state.boundary.x = level_state.boundary.w - 160
            Camera2D.set_boundary(level_state.boundary)
            Camera2D.follow_node(self.player)
            bridge_gate: BridgeGate = self.main.get_child("Sprite")  # temp
            if bridge_gate:
                bridge_gate.set_closed()
            level_state.is_currently_transitioning_within_level = False
            # Temp wandering soul spawn
            wandering_soul = WanderingSoul.new()
            wandering_soul.position = Vector2(
                level_state.boundary.w - 32, level_state.floor_y
            )
            wandering_soul.z_index = 10
            self.main.add_child(wandering_soul)
        except GeneratorExit:
            pass
