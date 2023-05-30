from typing import Optional, List, Type

from src.characters.enemy_definitions import EnemyDefinition
from src.items import HealthRestoreItem


class LevelAreaType:
    NORMAL = "normal"
    POWER_UP = "power_up"
    BOSS = "boss"
    END = "end"


class LevelSection:
    def __init__(self, enemy_defs: List[EnemyDefinition]):
        self.enemy_defs = enemy_defs
        self.index: Optional[int] = None


class LevelArea:
    """
    Area in a level separated by gates.  Can contain sections.
    """

    def __init__(
        self,
        area_type: str,
        width: int,
        sections: List[LevelSection] = None,
        item_types: List[Type] = None,
    ):
        self.area_type = area_type
        self.width = width
        if not sections:
            sections = []
        self.sections = sections
        for i, section in enumerate(sections):
            section.index = i
        if not item_types:
            item_types = []
        self.item_types = item_types
        self.is_completed = False

    def is_section_last(self, section: LevelSection) -> bool:
        if self.sections:
            last_index = len(self.sections) - 1
            return self.sections[last_index] == section
        return False


class LevelAreaDefinitions:
    DEF_MAP = {
        1: LevelArea(
            area_type=LevelAreaType.POWER_UP, width=260, item_types=[HealthRestoreItem]
        ),
        2: LevelArea(
            area_type=LevelAreaType.NORMAL,
            width=896,
            sections=[
                LevelSection(enemy_defs=[EnemyDefinition.RABBIT()]),
                LevelSection(
                    enemy_defs=[EnemyDefinition.RABBIT(), EnemyDefinition.JESTER()]
                ),
                LevelSection(
                    enemy_defs=[EnemyDefinition.RABBIT(), EnemyDefinition.JESTER()]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.CROW(),
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.CROW(),
                    ]
                ),
            ],
        ),
        3: LevelArea(
            area_type=LevelAreaType.POWER_UP, width=160, item_types=[HealthRestoreItem]
        ),
        4: LevelArea(
            area_type=LevelAreaType.NORMAL,
            width=896,
            sections=[
                LevelSection(enemy_defs=[EnemyDefinition.RABBIT()]),
                LevelSection(
                    enemy_defs=[EnemyDefinition.RABBIT(), EnemyDefinition.JESTER()]
                ),
                LevelSection(
                    enemy_defs=[EnemyDefinition.RABBIT(), EnemyDefinition.JESTER()]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.CROW(),
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.CROW(),
                    ]
                ),
            ],
        ),
        5: LevelArea(
            area_type=LevelAreaType.BOSS,
            width=160,
        ),
        6: LevelArea(area_type=LevelAreaType.END, width=160),
    }

    @staticmethod
    def get_def(area_num: int) -> Optional[LevelArea]:
        return LevelAreaDefinitions.DEF_MAP.get(area_num, None)

    @staticmethod
    def is_valid_area_index(index: int) -> bool:
        return index in LevelAreaDefinitions.DEF_MAP.keys()
