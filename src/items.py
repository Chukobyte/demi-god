from typing import Type

from crescent_api import *


class Item(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.sprite: Optional[Sprite] = None
        self.collider: Optional[Collider2D] = None
        self.description: Optional[str] = None
        self._description_split: Optional[List[str]] = None
        self.can_be_collected = True
        self.play_collected_sfx = True
        self.active = False

    def _start(self):
        self.sprite = Sprite.new()
        self.sprite.shader_instance = ShaderUtil.compile_shader(
            "shaders/outline.shader"
        )

        self._description_split = self._split_description_text()

    def _split_description_text(self, characters_per_line=19) -> List[str]:
        """
        Splits the item description text.  Max line is 19 characters long, for a total max of 38 characters.
        """
        # Early out if less than 19 characters
        if len(self.description) <= characters_per_line:
            return [self.description, ""]

        lines = []
        current_line = ""
        words = self.description.split()
        for word in words:
            if len(current_line + " " + word) > characters_per_line:
                lines.append(current_line.strip())
                current_line = word
            else:
                current_line += " " + word

        # Add last line to the array
        lines.append(current_line.strip())

        return lines

    def set_item_highlighted(self, is_highlighted: bool) -> None:
        if is_highlighted:
            outline_width = 0.8
        else:
            outline_width = 0.0
        self.sprite.shader_instance.set_float_param("outline_width", outline_width)

    @property
    def description_top(self) -> str:
        if len(self._description_split) == 0:
            return ""
        return self._description_split[0]

    @property
    def description_bottom(self) -> str:
        if len(self._description_split) <= 1:
            return ""
        return self._description_split[1]

    def collect(self) -> None:
        self.broadcast_event("collected", self)
        self.queue_deletion()


class ScrollItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Help the souls!"

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture("assets/images/items/item_scroll.png")
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        self.sprite.flip_h = True
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
        # Other
        self.position += Vector2(40, 0)


class HealthRestoreItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Restores health"
        self.restore_amount = 5

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture("assets/images/items/item_heart.png")
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)

        # self.position += Vector2(0, -4)


class EnergyDrainDecreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Lowers transform energy drain"

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture(
            "assets/images/items/item_energy_drain_decrease.png"
        )
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class DamageDecreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Reduces damage taken"

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture("assets/images/items/item_damage_decrease.png")
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class AttackRangeIncreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Increases attack range"

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture(
            "assets/images/items/item_attack_range_increase.png"
        )
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class SpecialAttackTimeDecreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Decrease special attack charge time"

    def _start(self):
        super()._start()
        size = Size2D(12, 12)
        # Sprite
        self.sprite.texture = Texture(
            "assets/images/items/item_special_attack_time_decrease.png"
        )
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class ItemUtils:
    @staticmethod
    def get_item_from_type(
        item_type: Type,
    ) -> HealthRestoreItem | ScrollItem | EnergyDrainDecreaseItem | DamageDecreaseItem | AttackRangeIncreaseItem | SpecialAttackTimeDecreaseItem | None:
        if issubclass(item_type, HealthRestoreItem):
            return HealthRestoreItem.new()
        elif issubclass(item_type, ScrollItem):
            return ScrollItem.new()
        elif issubclass(item_type, EnergyDrainDecreaseItem):
            return EnergyDrainDecreaseItem.new()
        elif issubclass(item_type, DamageDecreaseItem):
            return DamageDecreaseItem.new()
        elif issubclass(item_type, AttackRangeIncreaseItem):
            return AttackRangeIncreaseItem.new()
        elif issubclass(item_type, SpecialAttackTimeDecreaseItem):
            return SpecialAttackTimeDecreaseItem.new()
        print("ERROR: doesn't have item type in 'ItemUtils.get_item_from_type'!")
        return None

    @staticmethod
    def get_power_up_area_item_types() -> List[Type]:
        return [
            EnergyDrainDecreaseItem,
            DamageDecreaseItem,
            AttackRangeIncreaseItem,
            SpecialAttackTimeDecreaseItem,
        ]
