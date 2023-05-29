from crescent_api import *


class Item(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.color_rect: Optional[ColorRect] = None
        self.collider: Optional[Collider2D] = None
        self.description: Optional[str] = None


class AttackItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Add to attack"

    def _start(self):
        size = Size2D(8, 8)
        # Color Rect
        self.color_rect = ColorRect.new()
        self.color_rect.size = size
        self.color_rect.color = Color.RED()
        self.add_child(self.color_rect)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)


class HealthRestoreItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Add to attack"
        self.restore_amount = 2

    def _start(self):
        size = Size2D(8, 8)
        # Color Rect
        self.color_rect = ColorRect.new()
        self.color_rect.size = size
        self.color_rect.color = Color.RED()
        self.add_child(self.color_rect)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
