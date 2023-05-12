from typing import List, Optional

from src.characters.enemy_definitions import EnemyDefinition


class LevelAreaType:
    NORMAL = "normal"
    POWER_UP = "power_up"
    BOSS = "boss"


class LevelArea:
    def __init__(self, width: int, enemy_defs: List[EnemyDefinition]):
        self.width = width
        self.enemy_defs = enemy_defs


class LevelAreaDefinitions:
    DEF_MAP = {1: LevelArea(width=448, enemy_defs=[EnemyDefinition.RABBIT()])}

    @staticmethod
    def get_def(area_num: int) -> Optional[LevelArea]:
        return LevelAreaDefinitions.DEF_MAP.get(area_num, None)


class LevelAreaManager:
    def setup_level_area(self, area: LevelArea) -> None:
        pass
