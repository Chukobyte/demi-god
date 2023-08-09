import copy
import random
from typing import Optional, List, Type

from crescent_api import GameProperties

from src.characters.enemy_definitions import EnemyDefinition
from src.characters.player_item_handler import PlayerItemHandler
from src.characters.player_stats import PlayerStats
from src.items import *


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

    def get_random_item_types(
        self,
        player_stats: Optional[PlayerStats] = None,
        player_item_handler: Optional[PlayerItemHandler] = None,
        max_item_types=3,
    ) -> List[Type]:
        random_item_types = []
        item_types_copy = self.item_types[:]
        random.shuffle(item_types_copy)
        is_player_health_full = player_stats and player_stats.hp >= player_stats.base_hp
        for i in range(max_item_types):
            # Always spawn health restore as the second item (or middle if default is 3)
            if (
                i == 1
                and self.spawn_health_restore_for_middle_item
                and not is_player_health_full
            ):
                random_item_types.append(HealthRestoreItem)
            else:
                if item_types_copy:
                    potential_item_type = item_types_copy.pop()
                    if (
                        player_item_handler
                        and potential_item_type in player_item_handler.held_unique_items
                    ):
                        continue
                    random_item_types.append(potential_item_type)
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
            item_types=[LeverItem],
            spawn_health_restore_for_middle_item=False,
        ),
        2: LevelArea(
            area_type=LevelAreaType.POWER_UP,
            width=GameProperties().game_resolution.w,
            item_types=[
                AbilitySlowTimeItem,
                AbilityDualSpecialItem,
                AbilityHoodFormItem,
            ],
        ),
        3: LevelArea(
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
        4: LevelArea(
            area_type=LevelAreaType.POWER_UP,
            width=GameProperties().game_resolution.w,
            item_types=ItemUtils.get_power_up_area_item_types(),
        ),
        5: LevelArea(
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
        6: LevelArea(
            area_type=LevelAreaType.POWER_UP,
            width=GameProperties().game_resolution.w,
            item_types=ItemUtils.get_power_up_area_item_types(),
        ),
        7: LevelArea(
            area_type=LevelAreaType.NORMAL,
            width=896,
            sections=[
                LevelSection(enemy_defs=[EnemyDefinition.SNAKE()]),
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
        8: LevelArea(
            area_type=LevelAreaType.POWER_UP,
            width=GameProperties().game_resolution.w,
            item_types=ItemUtils.get_power_up_area_item_types(),
        ),
        9: LevelArea(
            area_type=LevelAreaType.BOSS,
            width=GameProperties().game_resolution.w,
        ),
        10: LevelArea(
            area_type=LevelAreaType.END, width=GameProperties().game_resolution.w
        ),
    }

    @staticmethod
    def get_def(area_num: int) -> Optional[LevelArea]:
        return LevelAreaDefinitions.DEF_MAP.get(area_num, None).copy()

    @staticmethod
    def is_valid_area_index(index: int) -> bool:
        return index in LevelAreaDefinitions.DEF_MAP.keys()
