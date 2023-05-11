import random
from typing import Type

from crescent_api import *

from src.characters.player import Player
from src.characters.enemy_jester import EnemyJester
from src.characters.wandering_soul import WanderingSoul
from src.level_state import LevelState
from src.environment.bridge_gate import BridgeGate
from src.utils.game_math import Ease, Easer
from src.utils.task import *
from src.utils.timer import Timer


class EnemyScenePaths:
    RABBIT = "scenes/characters/enemy_rabbit.cscn"
    JESTER = "scenes/characters/enemy_jester.cscn"
    CROW = "scenes/characters/enemy_crow.cscn"
    BOSS = "scenes/characters/enemy_boss.cscn"

    SECTION_MAP = {
        1: [RABBIT],
        2: [RABBIT, JESTER],
        3: [RABBIT, JESTER],
        4: [RABBIT, JESTER, CROW],
        5: [RABBIT, JESTER, CROW],
    }


class EnemyManager:
    def __init__(self, main: Node2D, player: Player):
        self.main = main
        self.player = player
        self._spawned_enemies = []

    def _get_spawned_enemies_by_type(self, enemy_type: Type) -> list:
        enemies = []
        for enemy in self._spawned_enemies:
            if isinstance(enemy, enemy_type):
                enemies.append(enemy)
        return enemies

    def _randomly_spawn_enemy_wave(
        self, base_position: Vector2, section: int, total_sections=5
    ):
        x_range = MinMax(-96, 96)
        left_side_enemies = []
        right_side_enemies = []
        enemy_arrays = []
        if section <= 1:
            enemy_arrays.append(right_side_enemies)
        elif section >= total_sections:
            enemy_arrays.append(left_side_enemies)
        else:
            enemy_arrays.append(right_side_enemies)
            enemy_arrays.append(left_side_enemies)
        # Main
        scene_paths = EnemyScenePaths.SECTION_MAP.get(section, [EnemyScenePaths.RABBIT])
        scene_path = random.choice(scene_paths)
        # Determine enemy stuff
        if scene_path == EnemyScenePaths.RABBIT:
            number_of_enemies = section + random.randint(0, 2)
            for i in range(number_of_enemies):
                enemy_array = random.choice(enemy_arrays)
                enemy_array.append(scene_path)
        elif scene_path == EnemyScenePaths.JESTER:
            other_jesters = self._get_spawned_enemies_by_type(EnemyJester)
            other_jesters_count = len(other_jesters)
            if other_jesters_count == 0:
                enemy_array = random.choice(enemy_arrays)
                enemy_array.append(scene_path)
            elif len(other_jesters) == 1:
                # Determine which side the other jester is on
                other_jester: EnemyJester = other_jesters[0]
                if other_jester.position.x > self.player.position.x:
                    left_side_enemies.append(scene_path)
                else:
                    right_side_enemies.append(scene_path)
            else:
                print(
                    f"Not adding jesters because there are {other_jesters_count} of them!"
                )
        elif scene_path == EnemyScenePaths.CROW:
            number_of_enemies = random.randint(1, 3)
            for i in range(number_of_enemies):
                enemy_array = random.choice(enemy_arrays)
                enemy_array.append(scene_path)
        # Spawn enemies
        enemy_scene = SceneUtil.load_scene(scene_path)
        # LEFT
        left_base_pos = base_position + Vector2(x_range.min, 0)
        for i, path in enumerate(left_side_enemies):
            enemy = enemy_scene.create_instance()
            enemy.position = left_base_pos + Vector2(i * (x_range.min / 4), 0.0)
            enemy.z_index = self.player.z_index
            self.main.add_child(enemy)
            enemy.subscribe_to_event("destroyed", self.main, self._on_enemy_destroyed)
            self._spawned_enemies.append(enemy)
        # RIGHT
        right_base_pos = base_position + Vector2(x_range.max, 0)
        for i, path in enumerate(right_side_enemies):
            enemy = enemy_scene.create_instance()
            enemy.position = right_base_pos + Vector2(i * (x_range.max / 4), 0.0)
            enemy.z_index = self.player.z_index
            self.main.add_child(enemy)
            enemy.subscribe_to_event("destroyed", self.main, self._on_enemy_destroyed)
            self._spawned_enemies.append(enemy)

    @staticmethod
    def get_section(position: Vector2, horizontal_max=640, section_size=128) -> int:
        sections = int(horizontal_max / section_size)
        # Early out if position is above horizontal max
        if position.x >= horizontal_max:
            return sections
        for i in range(sections):
            if section_size * i <= position.x <= section_size * i + section_size:
                return i + 1
        print(f"ERROR: Didn't find correct section for position: {position}?")
        return 0

    def _on_enemy_destroyed(self, enemy: Node2D) -> None:
        self._spawned_enemies.remove(enemy)

    # --- TASKS --- #
    async def enemy_waves_task(self):
        try:
            wave_cooldown_timer = Timer(35.0)
            level_state = LevelState()
            total_sections = 5
            is_non_boss_waves_finished = False
            while not is_non_boss_waves_finished:
                wave_cooldown_timer.tick(
                    self.main.get_full_time_dilation_with_physics_delta()
                )
                player_pos = self.player.position
                current_section = self.get_section(
                    player_pos,
                    horizontal_max=level_state.boundary.w,
                    section_size=level_state.boundary.w / total_sections,
                )
                if current_section == total_sections:
                    is_non_boss_waves_finished = True
                if (
                    len(self._spawned_enemies) == 0
                    or wave_cooldown_timer.time_remaining <= 0.0
                    or is_non_boss_waves_finished
                ):
                    # print(
                    #     f"position: {player_pos}, section: {current_section}, camera_pos: {Camera2D.get_position()}"
                    # )
                    wave_cooldown_timer.reset()
                    await co_wait_seconds(random.uniform(0.5, 2.5))
                    # Set base spawn position x to camera viewport position plus half of game resolution
                    spawn_pos_x = Camera2D.get_position().x + 80
                    base_spawn_pos = Vector2(spawn_pos_x, level_state.floor_y)
                    self._randomly_spawn_enemy_wave(
                        base_position=base_spawn_pos,
                        section=current_section,
                        total_sections=total_sections,
                    )
                await co_suspend()
            # Boss
            enemy_boss_scene = SceneUtil.load_scene(EnemyScenePaths.BOSS)
            enemy_boss = enemy_boss_scene.create_instance()
            enemy_boss.z_index = self.player.z_index
            enemy_boss.position = Vector2(
                level_state.boundary.w - 32, level_state.floor_y
            )
            enemy_boss.subscribe_to_event(
                "destroyed", self.main, self._on_enemy_destroyed
            )
            self._spawned_enemies.append(enemy_boss)
            self.main.add_child(enemy_boss)
            # Temp spawn wandering soul, will spawn after beating the boss and enemies
            while len(self._spawned_enemies) > 0:
                await co_suspend()
            bridge_gate: BridgeGate = self.main.get_child("Sprite")  # temp
            if bridge_gate:
                bridge_gate.set_opened()
            while True:
                await co_suspend()
        except GeneratorExit:
            pass


class SpawnedCloud(Sprite):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.move_speed = random.randint(5, 15)
        self.move_dir = Vector2.RIGHT()
        self._elapsed_time = 0.0

    def _fixed_update(self, delta_time: float) -> None:
        self._elapsed_time += delta_time
        current_pos = self.position
        new_pos = (
            current_pos
            + Vector2(delta_time * self.move_speed, delta_time * self.move_speed)
            * self.move_dir
        )
        self.position = Ease.Cubic.ease_in_vec2(
            elapsed_time=self._elapsed_time,
            from_pos=current_pos,
            to_pos=new_pos,
            duration=self._elapsed_time + 0.1,
        )


class GameMaster:
    # Manages game state such as enemy spawning
    def __init__(self, main_node):
        self.main = main_node
        self.player: Optional[Player] = None
        self.spawned_clouds: List[SpawnedCloud] = []
        self.main_task = Task(coroutine=self._update_task())
        self.bridge_transition_task: Optional[Task] = None

    def update(self) -> None:
        self.main_task.resume()

    # --- TASKS --- #
    async def _update_task(self):
        player_start_pos = Vector2(20, 78)
        enemy_waves_task: Optional[Task] = None
        manage_clouds_task: Optional[Task] = None
        try:
            # TODO: put in main.py
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))

            manage_clouds_task = Task(coroutine=self._manage_clouds_task())

            # Shoot down player beam first
            player_beam_color_rect = ColorRect.new()
            player_beam_color_rect.color = Color(240, 247, 243)
            player_beam_color_rect.size = Size2D(4, 8)
            player_beam_color_rect.z_index = 3
            self.main.add_child(player_beam_color_rect)
            player_beam_timer = Timer(3.0)
            player_beam_easer = Easer(
                Vector2(player_start_pos.x, -8),
                player_start_pos,
                player_beam_timer.time,
                Ease.Cubic.ease_in_vec2,
            )
            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                player_beam_timer.tick(delta_time)
                manage_clouds_task.resume()
                if player_beam_timer.time_remaining > 0.0:
                    new_beam_pos = player_beam_easer.ease(delta_time)
                    player_beam_color_rect.position = new_beam_pos
                    await co_suspend()
                else:
                    player_beam_color_rect.queue_deletion()
                    break

            main_theme_audio_source = AudioManager.get_audio_source(
                "assets/audio/music/main_theme.wav"
            )
            AudioManager.play_sound(source=main_theme_audio_source, loops=True)

            player_scene = SceneUtil.load_scene("scenes/characters/player.cscn")
            self.player: Player = player_scene.create_instance()
            self.player.position = player_start_pos
            self.main.add_child(self.player)

            enemy_manager = EnemyManager(main=self.main, player=self.player)
            enemy_waves_task = Task(coroutine=enemy_manager.enemy_waves_task())
            level_state = LevelState()
            level_state.floor_y = self.player.position.y
            # Spawn bridge gate
            bridge_gate = BridgeGate.new()
            bridge_gate.position = Vector2(
                level_state.boundary.w - 10, level_state.floor_y - 31
            )
            bridge_gate.z_index = 2
            self.main.add_child(bridge_gate)

            while True:
                if level_state.is_gate_transition_queued:
                    if self.bridge_transition_task:
                        self.bridge_transition_task.close()
                    self.bridge_transition_task = Task(
                        coroutine=self._manage_bridge_transition_task()
                    )
                    level_state.is_gate_transition_queued = False
                if self.bridge_transition_task:
                    self.bridge_transition_task.resume()
                enemy_waves_task.resume()
                manage_clouds_task.resume()
                await co_suspend()
        except GeneratorExit:
            if enemy_waves_task:
                enemy_waves_task.close()
            if manage_clouds_task:
                manage_clouds_task.close()

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

    async def _manage_clouds_task(self):
        try:
            max_clouds = 10
            cloud_textures = [
                Texture(file_path="assets/images/environment/cloud_variation1.png"),
                Texture(file_path="assets/images/environment/cloud_variation2.png"),
                Texture(file_path="assets/images/environment/cloud_variation3.png"),
                Texture(file_path="assets/images/environment/cloud_variation4.png"),
            ]
            cloud_texture_draw_source = Rect2(0, 0, 32, 18)
            self.spawned_clouds.clear()
            # Spawn initial clouds
            clouds_to_spawn = max_clouds - len(self.spawned_clouds)
            camera_pos = Camera2D.get_position()
            for i in range(clouds_to_spawn):
                cloud = SpawnedCloud.new()
                cloud.texture = random.choice(cloud_textures)
                cloud.draw_source = cloud_texture_draw_source
                cloud.position = camera_pos + Vector2(
                    i * random.randint(5, 40), random.randint(0, 40)
                )
                cloud.z_index = 2
                self.spawned_clouds.append(cloud)
                self.main.add_child(cloud)
            while True:
                clouds_to_spawn = max_clouds - len(self.spawned_clouds)
                camera_pos = Camera2D.get_position()
                for i in range(clouds_to_spawn):
                    cloud = SpawnedCloud.new()
                    cloud.texture = random.choice(cloud_textures)
                    cloud.draw_source = cloud_texture_draw_source
                    cloud.position = camera_pos + Vector2(
                        i * random.randint(5, 40), random.randint(0, 40)
                    )
                    cloud.z_index = 2
                    self.spawned_clouds.append(cloud)
                    self.main.add_child(cloud)
                await co_wait_seconds(10.0)
        except GeneratorExit:
            pass
