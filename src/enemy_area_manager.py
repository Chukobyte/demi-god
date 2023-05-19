import random
from typing import Type, Dict

from crescent_api import *

from src.characters.enemy import Enemy
from src.characters.enemy_boss import EnemyBoss
from src.characters.enemy_crow import EnemyCrow
from src.characters.enemy_definitions import EnemyScenePaths, EnemyDefinition
from src.characters.enemy_jester import EnemyJester
from src.characters.enemy_rabbit import EnemyRabbit
from src.characters.player import Player
from src.level_area import LevelArea, LevelSection
from src.level_state import LevelState
from src.utils import game_math
from src.utils.task import co_wait_seconds, co_suspend, co_return
from src.utils.timer import Timer


class EnemyAreaManager:
    def __init__(self):
        self._spawned_enemies: List[Enemy] = []
        self._enemy_scene_cache: Dict[str, PackedScene] = {}
        for enemy_def in EnemyDefinition.ALL():
            self._enemy_scene_cache[enemy_def.scene_path] = SceneUtil.load_scene(
                enemy_def.scene_path
            )

    def _get_spawned_enemies_by_type(self, enemy_type: Type) -> list:
        enemies = []
        for enemy in self._spawned_enemies:
            if isinstance(enemy, enemy_type):
                enemies.append(enemy)
        return enemies

    def _on_enemy_destroyed(self, enemy: Enemy) -> None:
        self._spawned_enemies.remove(enemy)

    def _get_section_by_position(
        self, position: Vector2, area: LevelArea
    ) -> Optional[LevelSection]:
        section_count = len(area.sections)
        if section_count == 0:
            return None
        elif section_count == 1:
            return area.sections[0]
        section_width = area.width / section_count
        local_position_x = position.x - LevelState().boundary.x
        section_index = int(local_position_x / section_width)
        return area.sections[section_index]

    def _attempt_spawn_enemies(
        self, base_spawn_pos: Vector2, section: LevelSection, total_sections: int
    ) -> None:
        enemy_defs = section.enemy_defs[:]
        x_range = MinMax(-96, 96)
        spawn_attempt_finished = False
        player = Player.find_player()
        main_node = SceneTree.get_root()
        while not spawn_attempt_finished:
            random_enemy_def: EnemyDefinition = random.choice(enemy_defs)
            enemy_defs.remove(random_enemy_def)
            enemies_of_type_in_level = self._get_spawned_enemies_by_type(
                random_enemy_def.enemy_type
            )
            enemy_count = len(enemies_of_type_in_level)
            max_enemies_to_spawn = random_enemy_def.max_total_count - enemy_count
            max_enemies_to_spawn = game_math.clamp(
                max_enemies_to_spawn, 0, random_enemy_def.max_spawn_count
            )
            if (
                enemy_count < random_enemy_def.max_total_count
                and max_enemies_to_spawn > 0
            ):
                num_of_enemies_to_spawn = random.randint(1, max_enemies_to_spawn)
                # Adjust base spawn position to fall either on the left or right
                if section.index == 0:
                    x_modifier = x_range.max
                elif section.index == total_sections - 1:
                    x_modifier = x_range.min
                elif not random_enemy_def.balance_spawn_sides or enemy_count == 0:
                    x_modifier = random.choice([x_range.min, x_range.max])
                else:
                    left_side_count = 0
                    right_side_count = 0
                    player_pos = Player.find_player().position
                    for enemy in enemies_of_type_in_level:
                        if enemy.position.x > player_pos.x:
                            left_side_count += 1
                        else:
                            right_side_count += 1
                    if left_side_count > right_side_count:
                        x_modifier = x_range.max
                    elif right_side_count > left_side_count:
                        x_modifier = x_range.min
                    else:
                        x_modifier = random.choice([x_range.min, x_range.max])
                base_spawn_pos.x += x_modifier
                for i in range(num_of_enemies_to_spawn):
                    spawned_enemy: Enemy = self._enemy_scene_cache[
                        random_enemy_def.scene_path
                    ].create_instance()
                    spawned_enemy.position = base_spawn_pos + Vector2(
                        i * (x_modifier / 4), 0.0
                    )
                    spawned_enemy.z_index = player.z_index
                    main_node.add_child(spawned_enemy)
                    spawned_enemy.subscribe_to_event(
                        "destroyed", main_node, self._on_enemy_destroyed
                    )
                    self._spawned_enemies.append(spawned_enemy)
                spawn_attempt_finished = True
            if not enemy_defs:
                break

    async def manage_area(self, area: LevelArea):
        try:
            sections: List[LevelSection] = area.sections
            if not sections:
                await co_return()
            section_count = len(sections)
            level_state = LevelState()
            player = Player.find_player()
            update_timer = Timer(5.0)

            # Main enemy wave loop
            while True:
                delta_time = World.get_delta_time()
                if update_timer.tick(delta_time).has_stopped():
                    update_timer.reset()

                    spawn_pos_x = Camera2D.get_position().x + 80
                    current_section = self._get_section_by_position(
                        player.position, area
                    )
                    base_spawn_pos = Vector2(spawn_pos_x, level_state.floor_y)
                    self._attempt_spawn_enemies(
                        base_spawn_pos, current_section, section_count
                    )
                    if area.is_section_last(current_section):
                        break
                await co_suspend()
            while self._spawned_enemies:
                await co_suspend()
            area.is_completed = True
        except GeneratorExit:
            self._spawned_enemies.clear()
