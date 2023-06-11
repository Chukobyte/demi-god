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

    def collect(self) -> None:
        self.broadcast_event("collected")
        self.queue_deletion()


class SignItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Help the souls!"
        self.can_be_collected = False

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
        self.z_index = 2


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
        size = Size2D(16, 16)
        # Sprite
        self.sprite = Sprite.new()
        self.sprite.texture = Texture("assets/images/items/item_heart.png")
        self.sprite.draw_source = Rect2(0, 0, 16, 16)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)

        self.position += Vector2(0, -4)


class ItemUtils:
    @staticmethod
    def get_item_from_type(
        item_type: Type,
    ) -> AttackItem | HealthRestoreItem | SignItem | None:
        if issubclass(item_type, AttackItem):
            return AttackItem.new()
        elif issubclass(item_type, HealthRestoreItem):
            return HealthRestoreItem.new()
        elif issubclass(item_type, SignItem):
            return SignItem.new()
        return None
