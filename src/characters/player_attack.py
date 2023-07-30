from crescent_api import *

from src.characters.enemy import Enemy


class PlayerAttack(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.damage = 1
        self.collider: Optional[Collider2D] = None
        # self.color = Color(240, 247, 243, 40)
        self.size = Size2D(20, 5)
        self.life_time = 1.0
        self.direction: Optional[Vector2] = None
        self.damaged_enemies = []
        self.flip_h = False

    def _start(self) -> None:
        self.collider = Collider2D.new()
        # collider_size = self.size - Size2D(0, 1)
        collider_size = self.size - Size2D(0, 1)
        self.collider.extents = collider_size
        self.add_child(self.collider)

    def _fixed_update(self, delta_time: float) -> None:
        # Check collision first
        collisions = CollisionHandler.process_collisions(self.collider)
        for collider in collisions:
            collider_parent = collider.get_parent()
            if (
                issubclass(type(collider_parent), Enemy)
                and not collider_parent.is_destroyed
                and collider_parent not in self.damaged_enemies
            ):
                self.broadcast_event("hit_enemy", collider_parent)
                collider_parent.take_damage(self.damage)
                self.damaged_enemies.append(collider_parent)

        self.life_time -= delta_time
        if self.life_time <= 0.0:
            self.queue_deletion()


class PlayerMeleeAttack(PlayerAttack):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.life_time = 0.1
        self.size = Size2D(32, 8)
        self.sprite: Optional[Sprite] = None

    def _start(self) -> None:
        super()._start()
        self.sprite = Sprite.new()
        self.sprite.texture = Texture("assets/images/demi/demi_attack_slash.png")
        self.sprite.draw_source = Rect2(0, 0, self.size.w, self.size.h)
        self.sprite.flip_h = self.flip_h
        self.add_child(self.sprite)

    def set_attack_range(self, extra_range: int) -> None:
        # self.size += Size2D(extra_range, 0)
        pass

    def update_attack_offset(self, is_crouching: bool) -> None:
        if is_crouching:
            attack_y = 2
        else:
            attack_y = -6
        attack_dist_from_player = 0
        if self.flip_h:
            left_side_offset = Vector2(-30, 0)
            attack_pos_offset = (
                Vector2(-attack_dist_from_player, attack_y) + left_side_offset
            )
        else:
            attack_pos_offset = Vector2(attack_dist_from_player, attack_y)
        self.position = attack_pos_offset


class PlayerSpecialAttack(PlayerAttack):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        # self.color = Color(240, 247, 243, 255)

    def _start(self) -> None:
        super()._start()
        self.anim_sprite = AnimatedSprite.new()
        animation = Animation(
            name="main",
            speed=200,
            loops=True,
            frames=[
                AnimationFrame(
                    frame=0,
                    texture_path="assets/images/demi/demi_special_attack.png",
                    draw_source=Rect2(0, 0, self.size.w, self.size.h),
                )
            ],
        )
        self.anim_sprite.add_animation(animation)
        self.anim_sprite.flip_h = self.flip_h
        self.add_child(self.anim_sprite)

    def _fixed_update(self, delta_time: float) -> None:
        move_speed = 80
        self.add_to_position(
            Vector2(
                self.direction.x * move_speed * delta_time,
                self.direction.y * move_speed * delta_time,
            )
        )
        super()._fixed_update(delta_time)

    def update_attack_offset(self, is_crouching: bool, base_pos: Vector2) -> None:
        if is_crouching:
            attack_y = 2
        else:
            attack_y = -2
        attack_dist_from_player = 0
        if self.flip_h:
            left_side_offset = Vector2(-20, 0)
            attack_pos_offset = (
                Vector2(-attack_dist_from_player, attack_y) + left_side_offset
            )
        else:
            attack_pos_offset = Vector2(attack_dist_from_player, attack_y)
        self.position = base_pos + attack_pos_offset

    # TODO: Delete old as used for a reference
    # def update_attack_offset(self, is_crouching: bool, base_pos: Vector2) -> None:
    #     if is_crouching:
    #         attack_y = 2
    #     else:
    #         attack_y = -2
    #     attack_dist_from_player = 0
    #     if self.flip_h:
    #         # left_side_offset = Vector2(-12 + -attack_range, 0)
    #         # attack_pos_offset = Vector2(-12, attack_y) + left_side_offset
    #         left_side_offset = Vector2(-20, 0)
    #         attack_pos_offset = (
    #             Vector2(-attack_dist_from_player, attack_y) + left_side_offset
    #         )
    #         # attack_pos_offset.x += attack_dist_from_player / 2.0
    #     else:
    #         # attack_pos_offset = Vector2(12, attack_y)
    #         attack_pos_offset = Vector2(attack_dist_from_player, attack_y)
    #     self.position = base_pos + attack_pos_offset
