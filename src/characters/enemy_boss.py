from crescent_api import *

from src.characters.enemy import Enemy
from src.characters.player import Player, PlayerStance
from src.level_state import LevelState
from src.utils.game_math import Easer, Ease, map_to_range
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
    IDLE = "idle"
    JUMP_AND_ATTACK = "jump_attack"


class EnemyBoss(Enemy):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self._set_base_hp(8)
        self.move_dir = Vector2.RIGHT()
        self.state = EnemyBossState.OLD_MOVE_TASK
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.do_entrance_stuff = True
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
            if self.split_on_death:
                self.destroyed_split_task = Task(coroutine=self._destroyed_split_task())
            self.broadcast_event("destroyed", self)
        else:
            self.take_damage_task = Task(coroutine=self._take_damage_task())
        self.anim_sprite.shader_instance.set_float_param("flash_amount", 0.5)

    def _end(self) -> None:
        if self.health_bar_ui:
            self.health_bar_ui.queue_deletion()

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
                    if self.state == EnemyBossState.OLD_MOVE_TASK:
                        state_task = Task(coroutine=self._old_move_state_task(player))
                    elif self.state == EnemyBossState.IDLE:
                        state_task = Task(coroutine=self._idle_state_task(player))
                    elif self.state == EnemyBossState.JUMP_AND_ATTACK:
                        state_task = Task(
                            coroutine=self._jump_and_attack_state_task(player)
                        )
                    else:
                        print(f"ERROR: invalid boss state {self.state}")
                prev_state = self.state
                state_task.resume()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _old_move_state_task(self, player: Player) -> None:
        def _update_move_dir() -> None:
            if player.position.x > self.position.x:
                self.anim_sprite.flip_h = False
                self.move_dir = Vector2.RIGHT()
            else:
                self.anim_sprite.flip_h = True
                self.move_dir = Vector2.LEFT()

        try:
            move_speed = 30
            _update_move_dir()
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                self.position += self.move_dir * Vector2(
                    move_speed * delta_time, move_speed * delta_time
                )
                if self.position.distance_to(player.position) > 60:
                    _update_move_dir()
                await co_suspend()
        except GeneratorExit:
            pass

    async def _idle_state_task(self, player: Player) -> None:
        try:
            while True:
                await co_suspend()
        except GeneratorExit:
            pass

    async def _jump_and_attack_state_task(self, player: Player) -> None:
        try:
            while True:
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
            # Fill up health bar 1 point at a time
            health_gain_audio_source = AudioManager.get_audio_source(
                "assets/audio/sfx/health_gain.wav"
            )
            fill_hp_amount = 0
            while fill_hp_amount < self.base_hp:
                fill_hp_amount += 1
                self.health_bar_ui.update(self.base_hp, fill_hp_amount)
                AudioManager.play_sound(health_gain_audio_source)
                await co_suspend()
                await co_suspend()

        except GeneratorExit:
            pass
