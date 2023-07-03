import random

from crescent_api import *

from src.characters.enemy import Enemy, EnemyAttack
from src.level_state import LevelState
from src.utils.task import *
from src.utils.timer import Timer


class EnemyJesterState:
    FOLLOWING_PLAYER = "following"
    RETREATING_FROM_PLAYER = "retreating"
    READY_FOR_ATTACK = "attacking"


class EnemyJesterProjectile(EnemyAttack):
    def _start(self) -> None:
        self.move_speed = 40
        size = Size2D(4, 4)
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
        self.sprite = Sprite.new()
        self.sprite.position = Vector2(-2, -2)
        self.sprite.texture = Texture(
            file_path="assets/images/enemy_jester/enemy_jester_ball_attack.png"
        )
        self.sprite.draw_source = Rect2(0, 0, 8, 8)
        self.add_child(self.sprite)
        self.physics_update_task = Task(coroutine=self._physics_update_task())

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        try:
            # Go 3 frames at half speed to telegraph projectile
            full_move_speed = self.move_speed
            self.move_speed /= 2.0
            await co_suspend()
            await co_suspend()
            await co_suspend()
            self.move_speed = full_move_speed

            life_timer = Timer(15.0)
            while life_timer.time_remaining > 0.0:
                life_timer.tick(self.get_full_time_dilation_with_physics_delta())
                await co_suspend()
            self.queue_deletion()
        except GeneratorExit:
            self.physics_update_task = None


class EnemyJester(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        self._set_base_hp(2)
        self.state = EnemyJesterState.FOLLOWING_PLAYER
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.move_speed = 30
        self.move_dir = Vector2.RIGHT
        self.player: Optional[Node2D] = None
        self.level_state = LevelState()

    def _spawn_projectile_attack(self) -> None:
        attack = EnemyJesterProjectile.new()
        y_offset = random.choice([2, -10])  # 2 = low, -10 = high
        attack.position = self.position + Vector2(0, y_offset)
        attack.direction = self.move_dir
        attack.z_index = self.z_index + 1
        SceneTree.get_root().add_child(attack)

    def _determine_state(self, attack_range=MinMax(36, 40)) -> str:
        pos_to_check = Vector2(self.player.position.x, self.level_state.floor_y)
        distance_to_player = self.position.distance_to(pos_to_check)
        if attack_range.is_above(distance_to_player):
            return EnemyJesterState.FOLLOWING_PLAYER
        elif attack_range.is_below(distance_to_player):
            return EnemyJesterState.RETREATING_FROM_PLAYER
        return EnemyJesterState.READY_FOR_ATTACK

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        try:
            self.player = self._find_player()
            prev_state = None
            state_task: Optional[Task] = None
            if self.player.position.x > self.position.x:
                self.move_dir = Vector2.RIGHT
            else:
                anim_sprite = self.get_child("AnimatedSprite")
                anim_sprite.flip_h = True
                self.move_dir = Vector2.LEFT
            while True:
                # if self._is_outside_of_level_boundary():
                #     self.queue_deletion()
                #     await co_return()
                # Change state task if previous state doesn't match current
                if self.state != prev_state:
                    if state_task:
                        state_task.close()
                    if self.state == EnemyJesterState.FOLLOWING_PLAYER:
                        state_task = Task(coroutine=self._follow_player_task())
                    elif self.state == EnemyJesterState.RETREATING_FROM_PLAYER:
                        state_task = Task(coroutine=self._retreat_from_player_task())
                    elif self.state == EnemyJesterState.READY_FOR_ATTACK:
                        state_task = Task(coroutine=self._ready_for_attack_task())
                    else:
                        print(f"ERROR: {self.state} is in invalid state!")
                prev_state = self.state
                state_task.resume()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _follow_player_task(self) -> None:
        try:
            self.anim_sprite.play("walk")
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position += self.move_dir * Vector2(
                    self.move_speed * delta_time, self.move_speed * delta_time
                )
                self.state = self._determine_state()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _retreat_from_player_task(self) -> None:
        try:
            self.anim_sprite.play("walk")
            retreat_speed = self.move_speed - 10
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position -= self.move_dir * Vector2(
                    retreat_speed * delta_time, retreat_speed * delta_time
                )
                # 1/6 chance to randomly change to attack when retreating
                if random.randint(0, 5) == 0:
                    self.state = EnemyJesterState.READY_FOR_ATTACK
                else:
                    self.state = self._determine_state()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _ready_for_attack_task(self) -> None:
        try:
            self.anim_sprite.play("idle")
            has_attacked_once = False
            attack_timer = Timer(random.uniform(0.25, 2.0))
            while True:
                attack_timer.tick(self.get_full_time_dilation_with_physics_delta())
                if attack_timer.time_remaining <= 0.0:
                    # TODO: Temp telegraph, maybe make an anim later...
                    self.anim_sprite.modulate = Color(1000, 1000, 1000)
                    await co_wait_seconds(0.2)
                    self._spawn_projectile_attack()
                    attack_timer.time = random.uniform(0.25, 3.0)
                    attack_timer.reset()
                    self.anim_sprite.modulate = Color.WHITE
                    # Slight cooldown after attacking
                    await co_wait_seconds(0.25)
                    has_attacked_once = True
                if has_attacked_once:
                    self.state = self._determine_state()
                await co_suspend()
        except GeneratorExit:
            pass
