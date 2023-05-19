from typing import Type, List

from src.characters.enemy_boss import EnemyBoss
from src.characters.enemy_crow import EnemyCrow
from src.characters.enemy_jester import EnemyJester
from src.characters.enemy_rabbit import EnemyRabbit


class EnemyScenePaths:
    RABBIT = "scenes/characters/enemy_rabbit.cscn"
    JESTER = "scenes/characters/enemy_jester.cscn"
    CROW = "scenes/characters/enemy_crow.cscn"
    BOSS = "scenes/characters/enemy_boss.cscn"


class EnemyDefinition:
    """
    Abstract definition for enemies
    """

    def __init__(
        self,
        scene_path: str,
        enemy_type: Type,
        max_total_count: int,
        max_spawn_count=1,
        balance_spawn_sides=False,
    ):
        self.scene_path = scene_path
        self.enemy_type = enemy_type
        self.max_total_count = max_total_count
        self.max_spawn_count = max_spawn_count
        self.balance_spawn_sides = balance_spawn_sides

    @staticmethod
    def RABBIT() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.RABBIT,
            enemy_type=EnemyRabbit,
            max_total_count=6,
            max_spawn_count=3,
        )

    @staticmethod
    def JESTER() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.JESTER,
            enemy_type=EnemyJester,
            max_total_count=2,
            max_spawn_count=1,
            balance_spawn_sides=True,
        )

    @staticmethod
    def CROW() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.CROW,
            enemy_type=EnemyCrow,
            max_total_count=3,
            max_spawn_count=2,
        )

    @staticmethod
    def BOSS() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.BOSS, enemy_type=EnemyBoss, max_total_count=1
        )

    @staticmethod
    def ALL() -> List["EnemyDefinition"]:
        return [
            EnemyDefinition.RABBIT(),
            EnemyDefinition.JESTER(),
            EnemyDefinition.CROW(),
            EnemyDefinition.BOSS(),
        ]
