from crescent_api import *

from src.level_state import LevelState
from src.utils.task import Task, co_suspend, co_wait_seconds, co_wait_until


class EnemyAttack(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.damage = 0
        self.move_speed = 0
        self.direction = Vector2.ZERO
        self.physics_update_task: Optional[Task] = None
        self.collider: Optional[Collider2D] = None
        self.destroy_on_touch = True

    def _fixed_update(self, delta_time: float) -> None:
        if self.physics_update_task:
            self.physics_update_task.resume()
        if self.direction == Vector2.ZERO:
            return None
        self.add_to_position(
            Vector2(
                self.direction.x * self.move_speed * delta_time,
                self.direction.y * self.move_speed * delta_time,
            )
        )


class Enemy(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.base_hp = 0
        self.hp = 0
        self.destroy_on_touch = False
        self.can_attach_to_player = False
        self.is_attached_to_player = False
        self.current_attached_shakes = 0
        self.shakes_required_for_detach = 3
        self.is_destroyed = False
        self.anim_sprite: Optional[AnimatedSprite] = None
        self.physics_update_task: Optional[Task] = None
        self.take_damage_task: Optional[Task] = None
        self.destroyed_task: Optional[Task] = None
        self.destroyed_split_task: Optional[Task] = None
        self.knock_back_on_death = True
        self.split_on_death = True
        self.split_range = MinMax(0.6, 0.6)
        self.split_amount = 0.05

    def _start(self) -> None:
        self.anim_sprite: AnimatedSprite = self.get_child("AnimatedSprite")
        self.anim_sprite.shader_instance = ShaderUtil.compile_shader(
            "shaders/enemy.shader"
        )

    def _fixed_update(self, delta_time: float) -> None:
        if not self.is_destroyed:
            if self.physics_update_task:
                self.physics_update_task.resume()
        else:
            if self.destroyed_task:
                self.destroyed_task.resume()
            else:
                if not self.is_queued_for_deletion:
                    print(f"ERROR: Should be destroyed task for {self}")
            if self.destroyed_split_task:
                self.destroyed_split_task.resume()
        if self.take_damage_task:
            self.take_damage_task.resume()

    def take_damage(self, damage: int) -> None:
        if self.take_damage_task:
            self.take_damage_task.close()
            self.take_damage_task = None
        self.hp = max(self.hp - damage, 0)
        if self.hp == 0:
            self.is_destroyed = True  # Maybe we want a callback here for enemies?
            self.destroyed_task = Task(coroutine=self._destroyed_task())
            if self.split_on_death:
                self.destroyed_split_task = Task(coroutine=self._destroyed_split_task())
            self.broadcast_event("destroyed", self)
        else:
            self.take_damage_task = Task(coroutine=self._take_damage_task())
        self.anim_sprite.shader_instance.set_float_param("flash_amount", 0.5)

    def destroy(self) -> None:
        if not self.is_destroyed:
            self.is_destroyed = True
            self.broadcast_event("destroyed", self)
            self.queue_deletion()

    def _set_base_hp(self, hp: int) -> None:
        self.base_hp = hp
        self.hp = hp

    def _find_player(self) -> Node2D:
        return SceneTree.get_root().get_child("Player")

    def _is_outside_of_level_boundary(self, padding=Vector2(64.0, 64.0)) -> bool:
        level_boundary = LevelState().boundary
        position = self.position
        return (
            position.x < level_boundary.x - padding.x
            or position.x > level_boundary.w + padding.x
            or position.y < level_boundary.y - padding.y
            or position.y > level_boundary.h + padding.y
        )

    def _is_outside_of_camera_viewport(self, padding=Vector2(64.0, 64.0)) -> bool:
        position = self.position
        camera_pos = Camera2D.get_position()
        camera_dimension = Size2D(160 + camera_pos.x, 144 + camera_pos.y)
        return (
            position.x < camera_pos.x - padding.x
            or position.x > camera_dimension.w + padding.x
            or position.y < camera_pos.y - padding.y
            or position.y > camera_dimension.h + padding.y
        )

        # --- TASKS --- #

    async def _take_damage_task(self) -> None:
        try:
            shader_instance = self.anim_sprite.shader_instance
            shader_instance.set_float_param("flash_amount", 0.75)
            await co_suspend()
            shader_instance.set_float_param("flash_amount", 0.0)
        except GeneratorExit:
            pass

    async def _destroyed_task(self) -> None:
        try:
            self.anim_sprite.stop()
            if self.knock_back_on_death:
                player = self._find_player()
                knock_back_distance = 5
                if self.position.x > player.position.x:
                    knock_back_dir = Vector2.RIGHT
                else:
                    knock_back_dir = Vector2.LEFT
                knock_back_velocity = (
                    Vector2(knock_back_distance, knock_back_distance) * knock_back_dir
                )
                for i in range(2):
                    self.position += knock_back_velocity
                    await co_wait_until(lambda: World.get_time_dilation() > 0.0)
            shader_instance = self.anim_sprite.shader_instance
            shader_instance.set_float_param("flash_amount", 0.75)
            await co_suspend()
            self.anim_sprite.modulate = Color(255, 255, 255, 200)
            shader_instance.set_float_param("flash_amount", 0.5)
            await co_wait_seconds(1.0)
            self.queue_deletion()
        except GeneratorExit:
            pass

    async def _destroyed_split_task(self) -> None:
        shader_instance = self.anim_sprite.shader_instance
        split = self.split_range

        def increment_split():
            split.min -= self.split_amount
            split.max += self.split_amount
            shader_instance.set_float_param("split_min", split.min)
            shader_instance.set_float_param("split_max", split.max)

        try:
            # Split enemy in half
            for i in range(50):
                increment_split()
                await co_wait_until(lambda: World.get_time_dilation() > 0.0)
        except GeneratorExit:
            pass
