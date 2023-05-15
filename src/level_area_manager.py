from typing import List, Optional

from crescent_api import *

from src.characters.enemy_definitions import EnemyDefinition
from src.characters.player import Player
from src.characters.wandering_soul import WanderingSoul
from src.environment.bridge_gate import BridgeGate
from src.level_clouds import LevelCloudManager
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

    @staticmethod
    def is_valid_area_index(index: int) -> bool:
        return index in LevelAreaDefinitions.DEF_MAP.keys()


class LevelAreaManager:
    def __init__(self):
        self.current_area_index = 0
        self.level_cloud_manager = LevelCloudManager()

    def setup_level_area(self, area: LevelArea) -> None:
        level_state = LevelState()
        level_state.boundary.w += area.width
        level_state.boundary.x = level_state.boundary.w - area.width
        Camera2D.set_boundary(level_state.boundary)

    def queue_next_area_transition(self) -> None:
        level_state = LevelState()
        level_state.is_gate_transition_queued = True
        level_state.is_currently_transitioning_within_level = True

    # --- TASKS --- #
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
                        coroutine=self._manage_bridge_transition_task(
                            self.level_cloud_manager
                        )
                    )
                if manage_bridge_transition_task:
                    manage_bridge_transition_task.resume()

                self.level_cloud_manager.update()
                await co_suspend()
        except GeneratorExit:
            pass

    async def beam_player_down(self, player_start_pos: Vector2):
        try:
            # Shoot down player beam first
            player_teleport_beam = Sprite.new()
            player_teleport_beam.texture = Texture(
                file_path="assets/images/demi/demi_teleport.png"
            )
            player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
            player_teleport_beam.origin = Vector2(25, 18)
            player_teleport_beam.z_index = 3
            SceneTree.get_root().add_child(player_teleport_beam)
            player_beam_timer = Timer(3.0)
            player_beam_easer = Easer(
                Vector2(player_start_pos.x, -20),
                player_start_pos,
                player_beam_timer.time,
                Ease.Cubic.ease_in_vec2,
            )
            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                player_beam_timer.tick(delta_time)
                self.level_cloud_manager.update()
                if player_beam_timer.time_remaining > 0.0:
                    new_beam_pos = player_beam_easer.ease(delta_time)
                    player_teleport_beam.position = new_beam_pos
                    await co_suspend()
                else:
                    # Hard code animation that delays 2 frames each
                    player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.queue_deletion()
                    break
        except GeneratorExit:
            pass

    async def _manage_bridge_transition_task(
        self, level_cloud_manager: LevelCloudManager
    ):
        try:
            player: Player = SceneTree.get_root().get_child("Player")
            self.current_area_index += 1
            next_level_area = LevelAreaDefinitions.get_def(self.current_area_index)
            is_last_area = LevelAreaDefinitions.is_valid_area_index(
                self.current_area_index + 1
            )
            level_state = LevelState()
            prev_player_time_dilation = player.time_dilation
            player.time_dilation = 0.0
            level_cloud_manager.set_clouds_time_dilation(0.0)
            level_state.boundary.w += next_level_area.width
            Camera2D.unfollow_node(player)
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

            initial_player_pos = player.position
            player_dest_pos = initial_player_pos + Vector2(30, 0)
            player_pos_easer = Easer(
                initial_player_pos,
                player_dest_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            await co_wait_seconds(1.0)
            player.time_dilation = prev_player_time_dilation
            player.play_animation("walk")
            level_cloud_manager.set_clouds_time_dilation(1.0)

            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                transition_timer.tick(delta_time)
                if transition_timer.time_remaining <= 0.0:
                    Camera2D.set_position(dest_camera_pos)
                    player.position = player_dest_pos
                    break
                else:
                    new_camera_pos = camera_pos_easer.ease(delta_time)
                    Camera2D.set_position(new_camera_pos)
                    new_player_pos = player_pos_easer.ease(delta_time)
                    player.position = new_player_pos
                await co_suspend()
            level_state.boundary.x = level_state.boundary.w - next_level_area.width
            Camera2D.set_boundary(level_state.boundary)
            Camera2D.follow_node(player)
            bridge_gate: BridgeGate = SceneTree.get_root().get_child("Sprite")  # temp
            if bridge_gate:
                bridge_gate.set_closed()
            level_state.is_currently_transitioning_within_level = False
            # Temp wandering soul spawn
            # wandering_soul = WanderingSoul.new()
            # wandering_soul.position = Vector2(
            #     level_state.boundary.w - 32, level_state.floor_y
            # )
            # wandering_soul.z_index = 10
            # self.main.add_child(wandering_soul)
        except GeneratorExit:
            pass
