from crescent_api import *


class WanderingSoul(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        self.collider: Optional[Collider2D] = None
        self.flip_h = False

    def _start(self) -> None:
        self.anim_sprite = self.get_child("AnimatedSprite")
        if self.anim_sprite:
            self.anim_sprite.flip_h = self.flip_h
