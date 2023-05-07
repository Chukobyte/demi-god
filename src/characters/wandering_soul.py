from crescent_api import *


class WanderingSoul(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.color_rect: Optional[ColorRect] = None
        self.collider: Optional[Collider2D] = None

    def _start(self) -> None:
        size = Size2D(8, 8)
        self.color_rect = ColorRect.new()
        self.color_rect.size = size
        self.add_child(self.color_rect)
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
