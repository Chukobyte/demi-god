from crescent_api import *

from src.characters.player import Player, PlayerStance
from src.characters.wandering_soul import WanderingSoul
from src.enemy_area_manager import EnemyAreaManager
from src.environment.bridge_gate import BridgeGate
from src.level_area import LevelAreaDefinitions, LevelArea, LevelAreaType
from src.level_clouds import LevelCloudManager
from src.level_state import LevelState
from src.items import AttackItem, ItemUtils
from src.utils.game_math import Easer, Ease
from src.utils.task import co_suspend, co_wait_seconds, Task
from src.utils.timer import Timer


class LevelAreaManager:
    def __init__(self):
        self.current_area_index = 1
        self.level_cloud_manager = LevelCloudManager()
        self.enemy_area_manager = EnemyAreaManager()
        self._manage_level_areas_task = Task(coroutine=self.manage_level_areas())
        self._manage_enemy_area_task: Optional[Task] = None
        self._current_area: Optional[LevelArea] = None
        self._has_processed_current_area_completion = False

    def update(self) -> None:
        self._manage_level_areas_task.resume()

    def _set_current_area(self, area: LevelArea) -> None:
        self._current_area = area
        self._has_processed_current_area_completion = False

    def _setup_area_type(self, area: LevelArea, level_state: LevelState) -> None:
        if area.area_type == LevelAreaType.POWER_UP:
            item_type = area.item_types[0]
            attack_item = ItemUtils.get_item_from_type(item_type)
            attack_item.position = Vector2(
                level_state.boundary.w - 80, level_state.floor_y
            )
            attack_item.z_index = 10
            SceneTree.get_root().add_child(attack_item)
        # Temp wandering soul spawn
        elif area.area_type == LevelAreaType.END:
            wandering_soul = WanderingSoul.new()
            wandering_soul.position = Vector2(
                level_state.boundary.w - 32, level_state.floor_y
            )
            wandering_soul.z_index = 10
            SceneTree.get_root().add_child(wandering_soul)

    # --- TASKS --- #
    async def manage_level_areas(self):
        try:
            level_state = LevelState()
            manage_bridge_transition_task: Optional[Task] = None

            # Set initial area
            self._set_current_area(
                LevelAreaDefinitions.get_def(self.current_area_index)
            )
            level_state.boundary.w += self._current_area.width
            Camera2D.set_boundary(level_state.boundary)
            # Set initial bridge gate
            level_state.bridge_gate_helper.spawn_bridge_gates()
            bridge_gate = level_state.bridge_gate_helper.next_bridge_gate()
            bridge_gate.position = Vector2(
                level_state.boundary.w - 10, level_state.floor_y - 31
            )

            self._setup_area_type(self._current_area, level_state)

            self._manage_enemy_area_task = Task(
                coroutine=self.enemy_area_manager.manage_area(self._current_area)
            )

            while True:
                # Need to handle waves for an area
                if self._manage_enemy_area_task:
                    self._manage_enemy_area_task.resume()

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

                if (
                    self._current_area
                    and self._current_area.is_completed
                    and not self._has_processed_current_area_completion
                ):
                    current_bridge_gate = (
                        level_state.bridge_gate_helper.get_current_bridge_gate()
                    )
                    current_bridge_gate.set_opened()
                    self._has_processed_current_area_completion = True
                await co_suspend()
        except GeneratorExit:
            pass

    async def beam_player_down(self, player_start_pos: Vector2):
        try:
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
                delta_time = World.get_delta_time()
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
            self._manage_enemy_area_task = None
            player = Player.find_player()
            self.current_area_index += 1
            next_level_area = LevelAreaDefinitions.get_def(self.current_area_index)
            is_last_area = not LevelAreaDefinitions.is_valid_area_index(
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
                level_state.boundary.w - next_level_area.width, initial_camera_pos.y
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
            if player.stance == PlayerStance.STANDING:
                player.play_animation("walk")
            level_cloud_manager.set_clouds_time_dilation(1.0)

            # Setup next bridge gate
            next_bridge_gate: Optional[BridgeGate] = None
            if not is_last_area:
                next_bridge_gate = level_state.bridge_gate_helper.next_bridge_gate()
                next_bridge_gate.set_closed()
                next_bridge_gate.position = Vector2(
                    level_state.boundary.w - 10, level_state.floor_y - 31
                )

            while True:
                delta_time = World.get_delta_time()
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

            level_state.bridge_gate_helper.close_gates()

            level_state.is_currently_transitioning_within_level = False
            self._setup_area_type(next_level_area, level_state)

            self._set_current_area(next_level_area)
            self._manage_enemy_area_task = Task(
                coroutine=self.enemy_area_manager.manage_area(next_level_area)
            )
        except GeneratorExit:
            pass
