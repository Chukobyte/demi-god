from crescent_api import *


class BridgeGate(Sprite):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._collider: Optional[Collider2D] = None
        self.size = BridgeGate.get_default_size()
        self.is_opened = False
        self.has_player_ever_stepped_through = False

    @staticmethod
    def get_default_size() -> Size2D:
        return Size2D(20, 100)

    def _start(self) -> None:
        self._collider = Collider2D.new()
        self._collider.extents = self.size
        self.add_child(self._collider)
        self.texture = Texture(file_path="assets/images/environment/bridge_gate.png")
        self.set_closed()

    def set_opened(self) -> None:
        self.draw_source = Rect2(self.size.w, 0, self.size.w, self.size.h)
        self.is_opened = True

    def set_closed(self) -> None:
        self.draw_source = Rect2(0, 0, self.size.w, self.size.h)
        self.is_opened = False
        self.has_player_ever_stepped_through = False
