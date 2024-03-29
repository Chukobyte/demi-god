from crescent_api import *

from src.characters.player import Player, PlayerStance
from src.characters.wandering_soul import WanderingSoul
from src.enemy_area_manager import EnemyAreaManager
from src.environment.bridge_gate import BridgeGate
from src.items import ItemUtils, Item, LeverItem
from src.level_area import LevelAreaDefinitions, LevelArea
from src.level_area_type import LevelAreaType
from src.level_clouds import LevelCloudManager
from src.level_state import LevelState
from src.utils.game_math import Easer, Ease
from src.utils.task import co_suspend, co_wait_seconds, Task, co_return
from src.utils.timer import Timer


class LevelAreaManager:
    def __init__(self):
        self.current_area_index = 1
        self.level_cloud_manager = LevelCloudManager()
        self.enemy_area_manager = EnemyAreaManager()
        self._manage_level_areas_task = Task(coroutine=self.manage_level_areas())
        self._manage_enemy_area_task: Optional[Task] = None
        self._current_area: Optional[LevelArea] = None
        self._choose_item_label: Optional[TextLabel] = None
        self._has_processed_current_area_completion = False
        self._game_ending_requested = False
        self._power_up_items: List[Item] = []

    def update(self) -> None:
        self._manage_level_areas_task.resume()

    def _on_item_activated(self, item) -> None:
        self._current_area.set_completed(True)
        try:
            self._power_up_items.remove(item)
        except ValueError as e:
            pass
        for item in self._power_up_items:
            item.queue_deletion()
        self._power_up_items.clear()

    def _on_last_area_item_completed(self, item) -> None:
        self._game_ending_requested = True

    def _set_current_area(self, area: LevelArea) -> None:
        self._current_area = area
        self._has_processed_current_area_completion = False

    def _setup_area_type(self, area: LevelArea, level_state: LevelState) -> None:
        level_state.current_level_area_type = area.area_type
        if (
            area.area_type == LevelAreaType.POWER_UP
            or area.area_type == LevelAreaType.INTRO
        ):
            main_node = SceneTree.get_root()
            player = Player.find_player()
            player_stats = None
            player_item_handler = None
            if player:
                player_stats = player.stats
                player_item_handler = player.item_handler
            random_item_types = area.get_random_item_types(
                player_stats, player_item_handler
            )
            item_offset = Vector2.ZERO
            for i, item_type in enumerate(random_item_types):
                power_up_item = ItemUtils.get_item_from_type(item_type)
                # Only expected to collect one item per power up area, which completes the area
                power_up_item.subscribe_to_event(
                    event_id="activated",
                    scoped_node=main_node,
                    callback_func=lambda item: self._on_item_activated(item),
                )
                power_up_item.position = (
                    Vector2(
                        level_state.boundary.w - 120 + (i * 40), level_state.floor_y - 1
                    )
                    + item_offset
                )
                power_up_item.z_index = 10
                main_node.add_child(power_up_item)
                self._power_up_items.append(power_up_item)
            if area.area_type != LevelAreaType.INTRO:
                # Add choose item label
                self._choose_item_label = TextLabel.new()
                self._choose_item_label.position = Vector2(40, 40)
                self._choose_item_label.z_index = 20
                self._choose_item_label.ignore_camera = True
                self._choose_item_label.font_uid = "gameboy-8"
                self._choose_item_label.text = "Choose One"
                main_node.add_child(self._choose_item_label)
        elif area.area_type == LevelAreaType.BOSS:
            player = Player.find_player()
            player.play_animation("idle")
            # The boss is expected to set this to False after entrance
            level_state.is_paused_from_boss = True
        # Temp wandering soul spawn
        elif area.area_type == LevelAreaType.END:
            main_node = SceneTree.get_root()
            lever_item = LeverItem.new()
            lever_item.subscribe_to_event(
                event_id="activated",
                scoped_node=main_node,
                callback_func=lambda item: self._on_last_area_item_completed(item),
            )
            lever_item.position = Vector2(
                level_state.boundary.w - 128, level_state.floor_y - 1
            )
            lever_item.z_index = 10
            main_node.add_child(lever_item)

    def _get_next_bridge_gate_position(self) -> Vector2:
        level_state = LevelState()
        bridge_gate_size = BridgeGate.get_default_size()
        return Vector2(
            level_state.boundary.w - (bridge_gate_size.w / 2),
            level_state.floor_y - (bridge_gate_size.h - 22),
        )

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
            bridge_gate.position = self._get_next_bridge_gate_position()

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
                        coroutine=self._manage_bridge_transition_task()
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

                    if self._choose_item_label:
                        self._choose_item_label.queue_deletion()
                        self._choose_item_label = None

                    self._has_processed_current_area_completion = True
                elif self._game_ending_requested:
                    await Task(coroutine=self._manage_game_end())
                    await co_return()
                await co_suspend()
        except GeneratorExit:
            pass

    async def beam_player_down(self, player_start_pos: Vector2):
        player_teleport_beam: Optional[Sprite] = None
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
                    beam_draw_source = Rect2(0, 0, 48, 48)
                    draw_sources: List[Rect2] = [
                        Rect2(
                            beam_draw_source.w,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                        Rect2(
                            beam_draw_source.w * 2.0,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                        Rect2(
                            beam_draw_source.w,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                        Rect2(
                            beam_draw_source.w * 2.0,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                        Rect2(
                            beam_draw_source.w * 3.0,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                        Rect2(
                            beam_draw_source.w * 4.0,
                            0,
                            beam_draw_source.w,
                            beam_draw_source.h,
                        ),
                    ]
                    # Hard code animation that delays 2 frames each
                    for draw_source in draw_sources:
                        player_teleport_beam.draw_source = draw_source
                        await co_suspend()
                        await co_suspend()
                    player_teleport_beam.queue_deletion()
                    player_teleport_beam = None

                    break
        except GeneratorExit:
            if player_teleport_beam:
                player_teleport_beam.queue_deletion()

    async def _manage_bridge_transition_task(self):
        try:
            if self._manage_enemy_area_task:
                self._manage_enemy_area_task.close()
                self._manage_enemy_area_task = None
            player = Player.find_player()
            self.current_area_index += 1
            next_level_area = LevelAreaDefinitions.get_def(self.current_area_index)
            level_state = LevelState()

            main_node = SceneTree.get_root()
            prev_time_dilation = main_node.time_dilation
            main_node.time_dilation = 0.0
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
            player_dest_pos = initial_player_pos + Vector2(40, 0)
            player_pos_easer = Easer(
                initial_player_pos,
                player_dest_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            await co_wait_seconds(1.0)
            main_node.time_dilation = prev_time_dilation
            if player.stance == PlayerStance.STANDING:
                player.play_animation("walk")

            # Setup next bridge gate
            next_bridge_gate = level_state.bridge_gate_helper.next_bridge_gate()
            next_bridge_gate.set_closed()
            next_bridge_gate.position = self._get_next_bridge_gate_position()

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

            prev_bridge = level_state.bridge_gate_helper.get_previous_bridge_gate()
            prev_bridge.set_closed()

            level_state.is_currently_transitioning_within_level = False
            self._setup_area_type(next_level_area, level_state)

            self._set_current_area(next_level_area)
            self._manage_enemy_area_task = Task(
                coroutine=self.enemy_area_manager.manage_area(next_level_area)
            )
        except GeneratorExit:
            pass

    async def _manage_game_end(self):
        try:
            player = Player.find_player()
            if player:
                player.input_enabled = False
                anim_name = player.get_current_animation_name()
                if "walk" in anim_name:
                    player.play_animation("idle")

            current_bridge_gate = (
                LevelState().bridge_gate_helper.get_current_bridge_gate()
            )
            current_bridge_gate.set_opened()

            # Spawn wandering souls
            level_state = LevelState()
            main_node = SceneTree.get_root()
            base_soul_pos = Vector2(
                level_state.boundary.w - 16, level_state.floor_y - 1
            )
            wandering_soul_scene = SceneUtil.load_scene(
                "scenes/characters/wandering_soul.cscn"
            )

            text_window = main_node.get_child("BottomUI").get_child("TextWindow")
            text_window.color = Color(255, 255, 255, 255)
            text_label_top: TextLabel = text_window.get_child("WindowTextTop")
            text_label_top.text = "You saved us!"

            dir_overrides = [
                Vector2(-0.95, -0.95),
                Vector2(-0.9, -1),
                Vector2(-1, -0.9),
                Vector2(-0.8, -1),
                Vector2(-1, -0.8),
                Vector2(-0.9, -0.9),
            ]
            for i in range(6):
                wandering_soul: WanderingSoul = wandering_soul_scene.create_instance()
                wandering_soul.position = base_soul_pos + Vector2(i * 4, 0)
                wandering_soul.z_index = 10
                wandering_soul.flip_h = True
                wandering_soul.move_dir = dir_overrides[i]
                main_node.add_child(wandering_soul)
                await co_wait_seconds(0.25)

            await co_wait_seconds(3.0)

            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=True))
            SceneTree.change_scene("scenes/end_game_screen.cscn")
        except GeneratorExit:
            pass
