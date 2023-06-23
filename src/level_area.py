import copy
import random
from typing import Optional, List, Type

from crescent_api import GameProperties

from src.characters.enemy_definitions import EnemyDefinition
from src.items import (
    HealthRestoreItem,
    SignItem,
    EnergyDrainDecreaseItem,
    DamageDecreaseItem,
    AttackRangeIncreaseItem,
)


class LevelAreaType:
    INTRO = "intro"
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
        spawn_health_restore_for_middle_item=True,
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
        self.spawn_health_restore_for_middle_item = spawn_health_restore_for_middle_item
        self.is_completed = False

    def set_completed(self, is_completed: bool) -> None:
        self.is_completed = is_completed

    def is_section_last(self, section: LevelSection) -> bool:
        if self.sections:
            last_index = len(self.sections) - 1
            return self.sections[last_index] == section
        return False

    def get_random_item_types(self, max_item_types=3) -> List[Type]:
        random_item_types = []
        item_types_count = len(self.item_types)
        if item_types_count == 1:
            random_item_types.append(self.item_types[0])
        else:
            item_types_copy = self.item_types[:]
            random.shuffle(item_types_copy)
            for i in range(max_item_types):
                # Always spawn health restore as the second item (or middle if default is 3)
                if i == 1 and self.spawn_health_restore_for_middle_item:
                    random_item_types.append(HealthRestoreItem)
                else:
                    if item_types_copy:
                        random_item_types.append(item_types_copy.pop())
                    else:
                        break
        return random_item_types

    def copy(self) -> "LevelArea":
        return copy.deepcopy(self)


class LevelAreaDefinitions:
    DEF_MAP = {
        1: LevelArea(
            area_type=LevelAreaType.INTRO,
            width=260,
            item_types=[SignItem],
            spawn_health_restore_for_middle_item=False,
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
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                    ]
                ),
            ],
        ),
        3: LevelArea(
            area_type=LevelAreaType.POWER_UP,
            width=GameProperties().game_resolution.w,
            item_types=[
                EnergyDrainDecreaseItem,
                DamageDecreaseItem,
                AttackRangeIncreaseItem,
            ],
        ),
        4: LevelArea(
            area_type=LevelAreaType.NORMAL,
            width=896,
            sections=[
                LevelSection(enemy_defs=[EnemyDefinition.SNAKE()]),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.SNAKE(),
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.SNAKE(),
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.SNAKE(),
                        EnemyDefinition.CROW(),
                    ]
                ),
                LevelSection(
                    enemy_defs=[
                        EnemyDefinition.RABBIT(),
                        EnemyDefinition.JESTER(),
                        EnemyDefinition.SNAKE(),
                        EnemyDefinition.CROW(),
                    ]
                ),
            ],
        ),
        5: LevelArea(
            area_type=LevelAreaType.BOSS,
            width=GameProperties().game_resolution.w,
        ),
        6: LevelArea(
            area_type=LevelAreaType.END, width=GameProperties().game_resolution.w
        ),
    }

    @staticmethod
    def get_def(area_num: int) -> Optional[LevelArea]:
        return LevelAreaDefinitions.DEF_MAP.get(area_num, None).copy()

    @staticmethod
    def is_valid_area_index(index: int) -> bool:
        return index in LevelAreaDefinitions.DEF_MAP.keys()
