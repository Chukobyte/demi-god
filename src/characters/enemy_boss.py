import random

from crescent_api import *

from src.characters.enemy import Enemy, EnemyAttack
from src.characters.player import Player, PlayerStance
from src.level_state import LevelState
from src.utils.game_math import Easer, Ease, map_to_range, clamp
from src.utils.task import *
from src.utils.timer import Timer


class BossHealthBarUI(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.border_color_rect: Optional[ColorRect] = None
        self.inner_health_color_rect: Optional[ColorRect] = None
        self.size = Size2D(64, 10)
        self._base_inner_health_color_rect_size = self.size - Size2D(2, 2)

    def _start(self) -> None:
        # Border
        self.border_color_rect = ColorRect.new()
        self.border_color_rect.ignore_camera = True
        self.border_color_rect.color = Color(2, 3, 2, 255)
        self.add_child(self.border_color_rect)
        # Inner Health Bar
        self.inner_health_color_rect = ColorRect.new()
        self.inner_health_color_rect.ignore_camera = True
        self.inner_health_color_rect.color = Color(163, 163, 163, 255)
        self.inner_health_color_rect.position += Vector2(1, 1)
        self.z_index += 1
        self.add_child(self.inner_health_color_rect)

        self._set_initial_size(self.size)

    def _set_initial_size(self, size: Size2D) -> None:
        self.size = size
        self.border_color_rect.size = size
        self._base_inner_health_color_rect_size = self.size - Size2D(2, 2)
        self.inner_health_color_rect.size = Size2D(
            0, self._base_inner_health_color_rect_size.h
        )

    def update(self, base_hp: int, hp: int) -> None:
        new_bar_width = map_to_range(
            hp, 0.0, base_hp, 0.0, self._base_inner_health_color_rect_size.w
        )
        self.inner_health_color_rect.size = Size2D(
            new_bar_width, self._base_inner_health_color_rect_size.h
        )


class EnemyBossState:
    OLD_MOVE_TASK = "move_task"
    JUMP_AND_ATTACK = "jump_attack"
    PROJECTILE_ATTACKS = "projectile_attacks"


class EnemyBossProjectile(EnemyAttack):
    def _start(self) -> None:
        self.move_speed = 40
        size = Size2D(4, 4)
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)
        self.sprite = Sprite.new()
        self.sprite.position = Vector2(-2, -2)
        # TODO: Use boss projectile sprite
        self.sprite.texture = Texture(
            file_path="assets/images/enemy_jester/enemy_jester_ball_attack.png"
        )
        self.sprite.draw_source = Rect2(0, 0, 8, 8)
        self.add_child(self.sprite)
        self.physics_update_task = Task(coroutine=self._physics_update_task())

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        try:
            # Go a certain amount frames at half speed to telegraph projectile
            frames_to_telegraph_attack = 6
            full_move_speed = self.move_speed
            self.move_speed /= 2.0
            for i in range(frames_to_telegraph_attack):
                await co_suspend()
            self.move_speed = full_move_speed

            life_timer = Timer(15.0)
            while life_timer.time_remaining > 0.0:
                life_timer.tick(self.get_full_time_dilation_with_physics_delta())
                await co_suspend()
            self.queue_deletion()
        except GeneratorExit:
            self.physics_update_task = None


class EnemyBoss(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(32)
        self.move_dir = Vector2.RIGHT
        self.state = EnemyBossState.OLD_MOVE_TASK
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.split_amount = 0.01
        self.do_entrance_stuff = True
        self.can_destroy_self = False  # Controlled from enemy area manager
        self.health_bar_ui: Optional[BossHealthBarUI] = None

    def _start(self) -> None:
        super()._start()
        self.anim_sprite.flip_h = True
        self.health_bar_ui = BossHealthBarUI.new()
        self.health_bar_ui.ignore_camera = True
        self.health_bar_ui.position = Vector2(53, 101)
        self.health_bar_ui.z_index = 10
        SceneTree.get_root().add_child(self.health_bar_ui)
        if self.do_entrance_stuff:
            self.position += Vector2(0, -101)
        else:
            self.position += Vector2(0, -1)

    def take_damage(self, damage: int) -> None:
        if self.take_damage_task:
            self.take_damage_task.close()
            self.take_damage_task = None
        self.hp = max(self.hp - damage, 0)
        self.health_bar_ui.update(self.base_hp, self.hp)
        if self.hp == 0:
            self.is_destroyed = True  # Maybe we want a callback here for enemies?
            self.destroyed_task = Task(coroutine=self._destroyed_task())
            self.broadcast_event("destroyed", self)
        else:
            self.take_damage_task = Task(coroutine=self._take_damage_task())
            self.anim_sprite.shader_instance.set_float_param("flash_amount", 0.5)

    def _end(self) -> None:
        if self.health_bar_ui:
            self.health_bar_ui.queue_deletion()

    def _face_player(self, player) -> None:
        if player.position.x > self.position.x:
            self.anim_sprite.flip_h = False
            self.move_dir = Vector2.RIGHT
        else:
            self.anim_sprite.flip_h = True
            self.move_dir = Vector2.LEFT

    def _spawn_projectile(self) -> EnemyBossProjectile:
        attack = EnemyBossProjectile.new()
        attack.set_owner(self)
        attack.direction = self.move_dir
        attack.z_index = self.z_index + 1
        return attack

    def _get_clamped_pos(
        self, position: Vector2, boundary: Rect2, padding=16
    ) -> Vector2:
        position.x = clamp(
            position.x,
            boundary.x + padding,
            boundary.w - padding,
        )
        return position

    # --- TASKS --- #
    async def _physics_update_task(self) -> None:
        try:
            player = Player.find_player()

            if self.do_entrance_stuff:
                landing_pos = self.position + Vector2(0, 100)
                await Task(coroutine=self._entrance_task(player, landing_pos))
            level_state = LevelState()
            level_state.is_paused_from_boss = False

            prev_state: Optional[str] = None
            state_task: Optional[Task] = None
            while True:
                if self.state != prev_state:
                    if state_task:
                        state_task.close()
                    if self.state == EnemyBossState.OLD_MOVE_TASK:
                        state_task = Task(coroutine=self._old_move_state_task(player))
                    elif self.state == EnemyBossState.JUMP_AND_ATTACK:
                        state_task = Task(
                            coroutine=self._jump_and_attack_state_task(player)
                        )
                    elif self.state == EnemyBossState.PROJECTILE_ATTACKS:
                        state_task = Task(
                            coroutine=self._projectile_attacks_state_task(player)
                        )
                    else:
                        print(f"ERROR: invalid boss state {self.state}")
                prev_state = self.state
                state_task.resume()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _old_move_state_task(self, player: Player) -> None:
        try:
            level_state = LevelState()
            move_speed = 25
            self._face_player(player)
            move_state_timer = Timer(random.uniform(1.5, 3.0))
            while True:
                if self._is_outside_of_camera_viewport(Vector2.ZERO):
                    self._face_player(player)
                delta_time = self.get_full_time_dilation_with_physics_delta()
                moved_pos = self.position + self.move_dir * Vector2(
                    move_speed * delta_time, move_speed * delta_time
                )
                moved_pos = self._get_clamped_pos(moved_pos, level_state.boundary)
                self.position = moved_pos
                # self.position += self.move_dir * Vector2(
                #     move_speed * delta_time, move_speed * delta_time
                # )
                move_state_timer.tick(delta_time)
                if move_state_timer.has_stopped():
                    self.state = EnemyBossState.PROJECTILE_ATTACKS
                await co_suspend()
        except GeneratorExit:
            pass

    async def _jump_and_attack_state_task(self, player: Player) -> None:
        try:
            level_state = LevelState()
            self._face_player(player)
            is_ascending = True
            jump_height = random.randint(35, 50)
            jump_speed = Vector2(random.randint(25, 50), -50)
            if self.move_dir == Vector2.LEFT:
                jump_speed.x *= -1
            # ASCEND
            while is_ascending:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                jump_vector = jump_speed * Vector2(delta_time, delta_time)
                new_pos = self.position + jump_vector
                new_pos.y = max(new_pos.y, level_state.floor_y - jump_height)
                self.position = self._get_clamped_pos(new_pos, level_state.boundary)
                if level_state.floor_y - self.position.y >= jump_height:
                    is_ascending = False
                await co_suspend()
            # ATTACK
            await co_wait_seconds(0.25)
            attack = self._spawn_projectile()
            attack.position = self.position
            attack.direction = self.position.direction_to(player.position)
            attack.move_speed = 60
            SceneTree.get_root().add_child(attack)
            await co_wait_seconds(0.1)
            # DESCENT
            is_descending = True
            jump_speed.y *= -1
            while is_descending:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                jump_vector = jump_speed * Vector2(delta_time, delta_time)
                new_pos = self.position + jump_vector
                new_pos.y = min(new_pos.y, level_state.floor_y)
                self.position = self._get_clamped_pos(new_pos, level_state.boundary)
                if self.position.y >= level_state.floor_y:
                    is_descending = False
                await co_suspend()
            self.state = EnemyBossState.OLD_MOVE_TASK
            await co_suspend()
        except GeneratorExit:
            pass

    async def _projectile_attacks_state_task(self, player: Player) -> None:
        try:
            self._face_player(player)
            await co_wait_seconds(1.0)

            # Random offsets either starting attack high or low (2 = low, -10 = high)
            y_offsets = random.choice([[2, -10, 2], [-10, 2, -10]])
            projectiles_to_spawn = 3
            for i in range(projectiles_to_spawn):
                self._face_player(player)
                attack = self._spawn_projectile()
                attack.position = self.position + Vector2(0, y_offsets[i])
                SceneTree.get_root().add_child(attack)
                await co_wait_seconds(1.0)
            self.state = EnemyBossState.JUMP_AND_ATTACK
            await co_suspend()
        except GeneratorExit:
            pass

    async def _entrance_task(self, player: Player, landing_pos: Vector2) -> None:
        try:
            # Last minute hack to make sure the player lands when entering boss room while in the air
            if player.stance == PlayerStance.IN_AIR:
                level_state = LevelState()
                player.input_enabled = False
                level_state.is_paused_from_boss = False
                while player.stance == PlayerStance.IN_AIR:
                    await co_suspend()
                player.input_enabled = True
                level_state.is_paused_from_boss = True

            # Fall from the sky and land
            landing_time = 5.0
            landing_timer = Timer(landing_time)
            enemy_landing_easer = Easer(
                self.position,
                landing_pos,
                landing_timer.time,
                Ease.Cubic.ease_out_vec2,
            )
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                landing_timer.tick(delta_time)
                if landing_timer.has_stopped():
                    self.position = landing_pos
                    break
                else:
                    self.position = enemy_landing_easer.ease(delta_time)
                await co_suspend()
            # TODO: Do anything else after landing, like an animation
            await co_suspend()
            await co_suspend()
            await co_suspend()
            # Fill up health bar in small increments at a time
            health_gain_audio_source = AudioManager.get_audio_source(
                "assets/audio/sfx/health_gain.wav"
            )
            fill_hp_amount = 0
            hp_increment_amount = int(self.base_hp / 8)
            while fill_hp_amount < self.base_hp:
                fill_hp_amount += hp_increment_amount
                self.health_bar_ui.update(self.base_hp, fill_hp_amount)
                AudioManager.play_sound(health_gain_audio_source)
                await co_suspend()
                await co_suspend()

        except GeneratorExit:
            pass

    async def _destroyed_task(self) -> None:
        try:
            self.anim_sprite.stop()
            while not self.can_destroy_self:
                await co_suspend()
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
                level_state = LevelState()
                for i in range(2):
                    self.position += knock_back_velocity
                    new_pos = self.position + knock_back_velocity
                    self._get_clamped_pos(new_pos, level_state.boundary)
                    await co_wait_until(lambda: World.get_time_dilation() > 0.0)
            shader_instance = self.anim_sprite.shader_instance
            shader_instance.set_float_param("flash_amount", 0.75)
            await co_suspend()
            self.anim_sprite.modulate = Color(255, 255, 255, 200)
            shader_instance.set_float_param("flash_amount", 0.5)
            # Slight delay before splitting
            await co_wait_seconds(1.0)
            await Task(coroutine=self._destroyed_split_task())
            self.queue_deletion()
        except GeneratorExit:
            pass
