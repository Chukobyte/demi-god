import random
from typing import Type

from crescent_api import *

from src.characters.enemy_definitions import EnemyScenePaths
from src.characters.enemy_jester import EnemyJester
from src.characters.player import Player
from src.environment.bridge_gate import BridgeGate
from src.level_state import LevelState
from src.utils.task import co_wait_seconds, co_suspend
from src.utils.timer import Timer

ENEMY_SECTION_MAP = {
    1: [EnemyScenePaths.RABBIT],
    2: [EnemyScenePaths.RABBIT, EnemyScenePaths.JESTER],
    3: [EnemyScenePaths.RABBIT, EnemyScenePaths.JESTER],
    4: [EnemyScenePaths.RABBIT, EnemyScenePaths.JESTER, EnemyScenePaths.CROW],
    5: [EnemyScenePaths.RABBIT, EnemyScenePaths.JESTER, EnemyScenePaths.CROW],
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
        scene_paths = ENEMY_SECTION_MAP.get(section, [EnemyScenePaths.RABBIT])
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
            print("Getting bridge gate")
            bridge_gate: BridgeGate = self.main.get_child("Sprite")  # temp
            if bridge_gate:
                print(f"Gotten: {bridge_gate}")
                bridge_gate.set_opened()
                print("Opened")
            while True:
                await co_suspend()
        except GeneratorExit:
            pass
