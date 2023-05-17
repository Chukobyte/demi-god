from typing import Type, List

from src.characters.enemy_rabbit import EnemyRabbit
from src.characters.enemy_jester import EnemyJester
from src.characters.enemy_crow import EnemyCrow
from src.characters.enemy_boss import EnemyBoss


class EnemyScenePaths:
    RABBIT = "scenes/characters/enemy_rabbit.cscn"
    JESTER = "scenes/characters/enemy_jester.cscn"
    CROW = "scenes/characters/enemy_crow.cscn"
    BOSS = "scenes/characters/enemy_boss.cscn"


class EnemyDefinition:
    """
    Abstract definition for enemies
    """

    def __init__(self, scene_path: str, enemy_type: Type):
        self.scene_path = scene_path
        self.enemy_type = enemy_type

    @staticmethod
    def RABBIT() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.RABBIT, enemy_type=EnemyRabbit
        )

    @staticmethod
    def JESTER() -> "EnemyDefinition":
        return EnemyDefinition(
            scene_path=EnemyScenePaths.JESTER, enemy_type=EnemyJester
        )

    @staticmethod
    def CROW() -> "EnemyDefinition":
        return EnemyDefinition(scene_path=EnemyScenePaths.CROW, enemy_type=EnemyCrow)

    @staticmethod
    def BOSS() -> "EnemyDefinition":
        return EnemyDefinition(scene_path=EnemyScenePaths.BOSS, enemy_type=EnemyBoss)
