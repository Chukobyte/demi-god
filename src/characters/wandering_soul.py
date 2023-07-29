from crescent_api import *


class WanderingSoul(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        self.flip_h = False

    def _start(self) -> None:
        self.anim_sprite = self.get_child("AnimatedSprite")
        if self.anim_sprite:
            self.anim_sprite.flip_h = self.flip_h

    def _fixed_update(self, delta_time: float) -> None:
        move_speed = 20
        direction = Vector2(-1, -1)
        self.add_to_position(
            Vector2(
                direction.x * move_speed * delta_time,
                direction.y * move_speed * delta_time,
            )
        )
