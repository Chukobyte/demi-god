from typing import Type

from crescent_api import *


class Item(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.color_rect: Optional[ColorRect] = None
        self.sprite: Optional[Sprite] = None
        self.collider: Optional[Collider2D] = None
        self.description: Optional[str] = None
        self.can_be_collected = True
        self.play_collected_sfx = True

    def collect(self) -> None:
        self.broadcast_event("collected", self)
        self.queue_deletion()


class ScrollItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Help the souls!"

    def _start(self):
        size = Size2D(10, 10)
        # Sprite
        self.sprite = Sprite.new()
        self.sprite.texture = Texture("assets/images/items/item_scroll.png")
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        self.sprite.flip_h = True
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
        self.z_index = 2
        # Other
        self.position += Vector2(40, 0)


class AttackItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Add to attack"

    def _start(self):
        size = Size2D(8, 8)
        # Color Rect
        self.color_rect = ColorRect.new()
        self.color_rect.size = size
        self.color_rect.color = Color.RED
        self.add_child(self.color_rect)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class HealthRestoreItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Restores health"
        self.restore_amount = 5

    def _start(self):
        size = Size2D(10, 10)
        # Sprite
        self.sprite = Sprite.new()
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
        self.description = "Lowers energy drain"

    def _start(self):
        size = Size2D(10, 10)
        # Sprite
        self.sprite = Sprite.new()
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
        self.description = "Reduces damage"

    def _start(self):
        size = Size2D(10, 10)
        # Sprite
        self.sprite = Sprite.new()
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
        self.description = "More attack range"

    def _start(self):
        size = Size2D(10, 10)
        # Sprite
        self.sprite = Sprite.new()
        self.sprite.texture = Texture(
            "assets/images/items/item_attack_range_increase.png"
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
    ) -> AttackItem | HealthRestoreItem | ScrollItem | EnergyDrainDecreaseItem | DamageDecreaseItem | AttackRangeIncreaseItem | None:
        if issubclass(item_type, AttackItem):
            return AttackItem.new()
        elif issubclass(item_type, HealthRestoreItem):
            return HealthRestoreItem.new()
        elif issubclass(item_type, ScrollItem):
            return ScrollItem.new()
        elif issubclass(item_type, EnergyDrainDecreaseItem):
            return EnergyDrainDecreaseItem.new()
        elif issubclass(item_type, DamageDecreaseItem):
            return DamageDecreaseItem.new()
        elif issubclass(item_type, AttackRangeIncreaseItem):
            return AttackRangeIncreaseItem.new()
        print("ERROR: doesn't have item type in 'ItemUtils.get_item_from_type'!")
        return None

    @staticmethod
    def get_power_up_area_item_types() -> List[Type]:
        return [EnergyDrainDecreaseItem, DamageDecreaseItem, AttackRangeIncreaseItem]
