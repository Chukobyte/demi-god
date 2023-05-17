from crescent_api import *
from src.characters.enemy import Enemy, EnemyAttack
from src.characters.wandering_soul import WanderingSoul
from src.level_state import LevelState
from src.environment.bridge_gate import BridgeGate
from src.utils.game_math import map_to_range, clamp, map_to_unit_range
from src.utils.task import *
from src.utils.timer import Timer


class PlayerAttack(ColorRect):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.damage = 1
        self.collider: Optional[Collider2D] = None
        self.color = Color(240, 247, 243, 40)
        self.size = Size2D(16, 4)
        self.life_time = 1.0
        self.direction: Optional[Vector2] = None
        self.damaged_enemies = []

    def _start(self) -> None:
        self.collider = Collider2D.new()
        self.collider.extents = self.size
        self.add_child(self.collider)

    def _fixed_update(self, delta_time: float) -> None:
        self.life_time -= delta_time
        if self.life_time <= 0.0:
            self.queue_deletion()
        else:
            collisions = CollisionHandler.process_collisions(self.collider)
            for collider in collisions:
                collider_parent = collider.get_parent()
                if (
                    issubclass(type(collider_parent), Enemy)
                    and not collider_parent.is_destroyed
                    and collider_parent not in self.damaged_enemies
                ):
                    self.broadcast_event("hit_enemy")
                    collider_parent.take_damage(self.damage)
                    self.damaged_enemies.append(collider_parent)


class PlayerMeleeAttack(PlayerAttack):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.life_time = 0.25


class PlayerSpecialAttack(PlayerAttack):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.damage = 2
        self.color = Color(240, 247, 243, 255)

    def _fixed_update(self, delta_time: float) -> None:
        move_speed = 80
        self.add_to_position(
            Vector2(
                self.direction.x * move_speed * delta_time,
                self.direction.y * move_speed * delta_time,
            )
        )
        super()._fixed_update(delta_time)


class PlayerStance:
    STANDING = "standing"
    CROUCHING = "crouching"
    IN_AIR = "in_air"


class PlayerStats:
    def __init__(self, base_hp=0.0, base_energy=0.0):
        self._hp = base_hp
        self._base_hp = base_hp
        self._energy = base_energy
        self._base_energy = base_energy
        self.health_bar_ui: Optional[ColorRect] = None
        self.energy_bar_ui: Optional[ColorRect] = None
        self.base_health_bar_ui_size = Size2D(52, 9)
        self.base_energy_bar_ui_size = Size2D(52, 9)

    def refresh_bar_nodes(self) -> None:
        main_node = SceneTree.get_root()
        self.health_bar_ui: ColorRect = main_node.get_child("HealthUI")
        self.energy_bar_ui: ColorRect = main_node.get_child("EnergyUI")

    @property
    def base_hp(self) -> float:
        return self._base_hp

    @property
    def hp(self) -> float:
        return self._hp

    @hp.setter
    def hp(self, value: float) -> None:
        self.set_hp(value)

    @property
    def base_energy(self) -> float:
        return self._base_energy

    @property
    def energy(self) -> float:
        return self._energy

    @energy.setter
    def energy(self, value: float) -> None:
        self.set_energy(value)

    def set_hp(self, hp: float) -> None:
        self._hp = clamp(hp, 0.0, self._base_hp)
        new_hp_bar_width = map_to_range(
            self._hp, 0.0, self._base_hp, 0.0, self.base_health_bar_ui_size.w
        )
        self.health_bar_ui.size = Size2D(
            new_hp_bar_width, self.base_health_bar_ui_size.h
        )

    def set_energy(self, energy: float) -> None:
        self._energy = clamp(energy, 0, self._base_energy)
        new_energy_bar_width = map_to_range(
            self._energy,
            0.0,
            self._base_energy,
            0.0,
            self.base_energy_bar_ui_size.w,
        )
        self.energy_bar_ui.size = Size2D(
            new_energy_bar_width, self.base_energy_bar_ui_size.h
        )


class Player(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        self.collider: Optional[Collider2D] = None
        self.stance = PlayerStance.STANDING
        self.stats = PlayerStats(base_hp=10, base_energy=20)
        self.move_speed = 25
        self.attack_requested = False
        self.special_attack_requested = False
        self.energy_attack_cost = 5
        self.is_transformed = False
        self.enemies_attached_to_left: List[Enemy] = []
        self.enemies_attached_to_right: List[Enemy] = []
        self.last_shake_dir = Vector2.ZERO()
        # Used when attacking to delay a frame on contact
        self.enemy_collision_invincible = False
        self.in_attack_damage_cooldown = False
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.transformation_task: Optional[Task] = None
        self.attack_slash_audio_source = AudioManager.get_audio_source(
            "assets/audio/sfx/attack_slash.wav"
        )
        self._current_animation_name = ""  # TODO: Add function to engine instead

    def _start(self) -> None:
        self.anim_sprite = self.get_child("AnimatedSprite")
        self.collider = self.get_child("Collider2D")
        self.stats.refresh_bar_nodes()
        level_state = LevelState()
        Camera2D.follow_node(self)
        # Start with 0 energy
        self.stats.energy = 0

    def _update(self, delta_time: float) -> None:
        # Pause game
        level_state = LevelState()
        if Input.is_action_just_pressed("start"):
            if not level_state.is_paused:
                World.set_time_dilation(0.0)
            else:
                World.set_time_dilation(1.0)
            level_state.is_paused = not level_state.is_paused

        if not self._are_enemies_attached() and not level_state.is_game_state_paused():
            if Input.is_action_just_pressed("attack"):
                self.attack_requested = True
            elif Input.is_action_just_pressed("special"):
                if self.is_transformed:
                    self.is_transformed = False
                    if self.transformation_task:
                        self.transformation_task.close()
                        self.transformation_task = None
                else:
                    # Transform if at max
                    if self.stats.energy == self.stats.base_energy:
                        self.is_transformed = True
                        self.transformation_task = Task(
                            coroutine=self._transformation_task()
                        )
                    elif self.stats.energy >= self.energy_attack_cost:
                        self.stats.energy -= self.energy_attack_cost
                        self.attack_requested = True
                        self.special_attack_requested = True

    def _fixed_update(self, delta_time: float) -> None:
        self.physics_update_task.resume()

    def play_animation(self, anim_name: str) -> None:
        self._current_animation_name = anim_name
        if self.is_transformed:
            self.anim_sprite.play(f"{anim_name}_t")
        else:
            self.anim_sprite.play(anim_name)

    def _are_enemies_attached(self) -> bool:
        return (
            len(self.enemies_attached_to_left) > 0
            or len(self.enemies_attached_to_right) > 0
        )

    def _get_attached_count(self) -> int:
        return len(self.enemies_attached_to_left) + len(self.enemies_attached_to_right)

    def _handle_attached_shake(self, new_shake_dir: Vector2) -> None:
        if self.last_shake_dir != new_shake_dir:
            for enemy in self.enemies_attached_to_left[:]:
                enemy.current_attached_shakes += 1
                if enemy.current_attached_shakes >= enemy.shakes_required_for_detach:
                    self.enemies_attached_to_left.remove(enemy)
                    enemy.destroy()
            for enemy in self.enemies_attached_to_right[:]:
                enemy.current_attached_shakes += 1
                if enemy.current_attached_shakes >= enemy.shakes_required_for_detach:
                    self.enemies_attached_to_right.remove(enemy)
                    enemy.destroy()
            if self._are_enemies_attached():
                self.last_shake_dir = new_shake_dir
            else:
                self.last_shake_dir = Vector2.ZERO()

    def _execute_attack(self) -> None:
        if self.stance == PlayerStance.CROUCHING:
            attack_y = 2
        else:
            attack_y = -2
        if self.anim_sprite.flip_h:
            left_side_offset = Vector2(-12, 0)
            attack_pos_offset = Vector2(-12, attack_y) + left_side_offset
            attack_dir = Vector2.LEFT()
        else:
            attack_pos_offset = Vector2(12, attack_y)
            attack_dir = Vector2.RIGHT()
        attack_pos = self.position + attack_pos_offset
        attack_z_index = self.z_index + 1
        if self.special_attack_requested:
            special_attack = PlayerSpecialAttack.new()
            special_attack.position = attack_pos
            special_attack.z_index = attack_z_index
            special_attack.direction = attack_dir
            SceneTree.get_root().add_child(special_attack)
            self.special_attack_requested = False
        else:
            melee_attack = PlayerMeleeAttack.new()
            melee_attack.subscribe_to_event(
                event_id="hit_enemy",
                scoped_node=self,
                callback_func=lambda args: self.stats.set_energy(self.stats.energy + 1),
            )
            melee_attack.position = attack_pos
            melee_attack.z_index = attack_z_index
            SceneTree.get_root().add_child(melee_attack)
        AudioManager.play_sound(source=self.attack_slash_audio_source)

    # --- TASKS --- #
    async def _physics_update_task(self):
        level_state = LevelState()
        take_damage_task = Task(coroutine=self._damage_check_task())
        prev_stance = None
        current_stance_task: Optional[Task] = None

        def get_new_stance_task() -> Optional[Task]:
            if self.stance == PlayerStance.STANDING:
                return Task(coroutine=self._stand_stance_task())
            elif self.stance == PlayerStance.CROUCHING:
                return Task(coroutine=self._crouch_stance_task())
            elif self.stance == PlayerStance.IN_AIR:
                return Task(coroutine=self._in_air_stance_task())
            return None

        try:
            while True:
                # Run take damage (collision) task first
                take_damage_task.resume()
                # Transformation task
                if self.transformation_task:
                    self.transformation_task.resume()
                    if self.stats.energy == 0:
                        self.is_transformed = False
                        self.transformation_task.close()
                        self.transformation_task = None
                # Change stance if different from last frame
                if prev_stance != self.stance:
                    if current_stance_task:
                        current_stance_task.close()
                    current_stance_task = get_new_stance_task()
                prev_stance = self.stance
                # Now run current stance task
                if current_stance_task and not level_state.is_game_state_paused():
                    current_stance_task.resume()
                await co_suspend()
        except GeneratorExit:
            if current_stance_task:
                current_stance_task.close()

    async def _damage_cooldown_task(
        self,
        cooldown_time: float,
        gamepad_vibration=True,
        hp_damage=1.0,
        modulate_color=True,
    ):
        def subtract_hp_value(damage: float, bar_color: Color) -> None:
            self.stats.hp -= damage
            self.stats.health_bar_ui.color = bar_color
            # TODO: Have game over state
            if self.stats.hp <= 0:
                SceneTree.change_scene("scenes/title_screen.cscn")

        try:
            if gamepad_vibration:
                Input.start_gamepad_vibration(0, 0.5, 0.5, 0.25)
            cooldown_timer = Timer(cooldown_time)
            normal_hp_bar_color = self.stats.health_bar_ui.color
            has_subtracted_health = False
            self.stats.health_bar_ui.color = Color(240, 247, 243)
            if modulate_color:
                self.anim_sprite.modulate = Color(255, 255, 255, 100)
            cooldown_timer.tick(self.get_full_time_dilation_with_physics_delta())
            await co_suspend()
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                cooldown_timer.tick(delta_time)
                if cooldown_timer.time_remaining > 0.0:
                    if not has_subtracted_health:
                        has_subtracted_health = True
                        subtract_hp_value(hp_damage, normal_hp_bar_color)
                    await co_suspend()
                else:
                    if modulate_color:
                        self.anim_sprite.modulate = Color(255, 255, 255, 255)
                    if not has_subtracted_health:
                        subtract_hp_value(hp_damage, normal_hp_bar_color)
                    break
        except GeneratorExit:
            pass

    async def _damage_check_task(self):
        try:
            damage_cooldown_task: Optional[Task] = None
            attached_damage_cooldown_task: Optional[Task] = None
            level_state = LevelState()
            while True:
                collisions = CollisionHandler.process_collisions(self.collider)
                for collider in collisions:
                    collider_parent = collider.get_parent()
                    collider_parent_type = type(collider_parent)
                    if collider_parent.is_queued_for_deletion:
                        continue
                    # Enemy Collision
                    if (
                        issubclass(collider_parent_type, Enemy)
                        and not self.enemy_collision_invincible
                        and not self.in_attack_damage_cooldown
                        and not collider_parent.is_destroyed
                    ):
                        if collider_parent.can_attach_to_player:
                            if not collider_parent.is_attached_to_player:
                                collider_parent.is_attached_to_player = True
                                if collider_parent.position.x > self.position.x:
                                    num_on_right = len(self.enemies_attached_to_right)
                                    floor_y = LevelState().floor_y
                                    collider_parent.position = Vector2(
                                        self.position.x, floor_y
                                    ) + Vector2(4 * (num_on_right + 1), 0)
                                    self.enemies_attached_to_right.append(
                                        collider_parent
                                    )
                                else:
                                    num_on_left = len(self.enemies_attached_to_left)
                                    floor_y = LevelState().floor_y
                                    collider_parent.position = (
                                        Vector2(self.position.x, floor_y)
                                        + Vector2(-2, 0)
                                        + Vector2(-4 * (num_on_left + 1), 0)
                                    )
                                    self.enemies_attached_to_left.append(
                                        collider_parent
                                    )
                        elif (
                            not self.enemy_collision_invincible
                            and not self.in_attack_damage_cooldown
                        ):
                            if collider_parent.destroy_on_touch:
                                collider_parent.destroy()
                            self.in_attack_damage_cooldown = True
                            damage_cooldown_task = Task(
                                coroutine=self._damage_cooldown_task(1.0)
                            )
                    # Enemy Attack Collision
                    elif (
                        issubclass(collider_parent_type, EnemyAttack)
                        and not self.enemy_collision_invincible
                        and not self.in_attack_damage_cooldown
                    ):
                        collider_parent.queue_deletion()
                        self.in_attack_damage_cooldown = True
                        damage_cooldown_task = Task(
                            coroutine=self._damage_cooldown_task(1.0)
                        )
                    # Temp level finish
                    elif issubclass(collider_parent_type, WanderingSoul):
                        SceneTree.change_scene("scenes/title_screen.cscn")
                        await co_return()
                        break
                    elif issubclass(collider_parent_type, BridgeGate):
                        bridge_gate: BridgeGate = collider_parent
                        if (
                            bridge_gate.is_opened
                            and not bridge_gate.has_player_ever_stepped_through
                        ):
                            bridge_gate.has_player_ever_stepped_through = True
                            level_state.queue_gate_transition()
                            # SceneTree.change_scene("scenes/title_screen.cscn")
                            # await co_return()
                            break
                if damage_cooldown_task:
                    if damage_cooldown_task.valid:
                        damage_cooldown_task.resume()
                    else:
                        self.in_attack_damage_cooldown = False
                        damage_cooldown_task = None
                # Check for attached damage
                num_of_attached = self._get_attached_count()
                if num_of_attached > 0:
                    if not attached_damage_cooldown_task or (
                        attached_damage_cooldown_task
                        and not attached_damage_cooldown_task.valid
                    ):
                        if attached_damage_cooldown_task:
                            attached_damage_cooldown_task.close()
                        attached_damage_cooldown_task = Task(
                            coroutine=self._damage_cooldown_task(
                                cooldown_time=0.25,
                                gamepad_vibration=False,
                                hp_damage=0.25 * num_of_attached,
                                modulate_color=False,
                            )
                        )
                    attached_damage_cooldown_task.resume()
                else:
                    if attached_damage_cooldown_task:
                        if attached_damage_cooldown_task.valid:
                            attached_damage_cooldown_task.close()
                        attached_damage_cooldown_task = None
                await co_suspend()
        except GeneratorExit:
            pass

    async def _attack_task(self):
        try:
            frame_count = 0
            self.enemy_collision_invincible = True
            self._execute_attack()
            attack_timer = Timer(0.25)
            while True:
                frame_count += 1
                if frame_count >= 2:
                    self.enemy_collision_invincible = False
                delta_time = self.get_full_time_dilation_with_physics_delta()
                attack_timer.tick(delta_time)
                if attack_timer.time_remaining <= 0.0:
                    break
                await co_suspend()
        except GeneratorExit:
            self.enemy_collision_invincible = False

    async def _transformation_task(self):
        try:
            transformation_tick_rate = 0.25
            energy_drain_per_tick = 1
            # Update animation to transformed
            self.play_animation(self._current_animation_name)
            while True:
                await co_wait_seconds(transformation_tick_rate)
                self.stats.energy -= energy_drain_per_tick
                await co_suspend()
        except GeneratorExit:
            self.play_animation(self._current_animation_name)

    async def _stand_stance_task(self):
        try:
            self.play_animation("idle")
            self.collider.position = Vector2(-6, -10)
            self.collider.extents = Size2D(12, 16)
            level_state = LevelState()
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                if self.attack_requested:
                    self.play_animation("stand_attack")
                    await self._attack_task()
                    self.attack_requested = False
                    self.play_animation("idle")
                else:
                    if Input.is_action_pressed("move_left"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.LEFT() * Vector2(
                                delta_time * self.move_speed,
                                delta_time * self.move_speed,
                            )
                            new_position.x = clamp(
                                new_position.x,
                                level_state.boundary.x,
                                level_state.boundary.w,
                            )
                            self.play_animation("walk")
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.LEFT())
                        self.anim_sprite.flip_h = True
                    elif Input.is_action_pressed("move_right"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.RIGHT() * Vector2(
                                delta_time * self.move_speed,
                                delta_time * self.move_speed,
                            )
                            new_position.x = clamp(
                                new_position.x,
                                level_state.boundary.x,
                                level_state.boundary.w,
                            )
                            self.play_animation("walk")
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.RIGHT())
                        self.anim_sprite.flip_h = False
                    else:
                        self.play_animation("idle")
                    if (
                        Input.is_action_pressed("jump")
                        and not self._are_enemies_attached()
                    ):
                        self.stance = PlayerStance.IN_AIR
                        await co_return()
                    elif (
                        Input.is_action_pressed("crouch")
                        and not self._are_enemies_attached()
                    ):
                        self.stance = PlayerStance.CROUCHING
                        await co_return()
                    await co_suspend()
        except GeneratorExit:
            pass

    async def _crouch_stance_task(self):
        try:
            self.play_animation("crouch")
            self.collider.position = Vector2(-6, -4)
            self.collider.extents = Size2D(12, 10)
            while True:
                if self.attack_requested:
                    self.play_animation("crouch_attack")
                    await self._attack_task()
                    self.attack_requested = False
                    self.play_animation("crouch")
                else:
                    if Input.is_action_pressed("move_left"):
                        if self._are_enemies_attached():
                            self._handle_attached_shake(Vector2.LEFT())
                        self.anim_sprite.flip_h = True
                    elif Input.is_action_pressed("move_right"):
                        if self._are_enemies_attached():
                            self._handle_attached_shake(Vector2.RIGHT())
                        self.anim_sprite.flip_h = False
                    if Input.is_action_pressed("jump"):
                        self.stance = PlayerStance.IN_AIR
                        await co_return()
                    elif not Input.is_action_pressed("crouch"):
                        self.stance = PlayerStance.STANDING
                        await co_return()
                    await co_suspend()
        except GeneratorExit:
            pass

    async def _in_air_stance_task(self):
        self.play_animation("idle")
        attack_task: Optional[Task] = None
        try:
            level_state = LevelState()
            jump_speed = 30
            jump_time = 1.0
            ascend_timer = Timer(jump_time / 2.0)
            descent_timer = Timer(jump_time / 2.0)
            is_ascending = True
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                if self.attack_requested and not attack_task:
                    attack_task = Task(coroutine=self._attack_task())
                    self.play_animation("stand_attack")
                    self.attack_requested = False
                if attack_task:
                    attack_task.resume()
                    if not attack_task.valid:
                        attack_task = None
                        self.play_animation("idle")
                if Input.is_action_pressed("move_left"):
                    if not self._are_enemies_attached():
                        new_position = self.position + Vector2.LEFT() * Vector2(
                            delta_time * self.move_speed,
                            delta_time * self.move_speed,
                        )
                        new_position.x = clamp(
                            new_position.x,
                            level_state.boundary.x,
                            level_state.boundary.w,
                        )
                        self.position = new_position
                    else:
                        self._handle_attached_shake(Vector2.LEFT())
                    self.anim_sprite.flip_h = True
                elif Input.is_action_pressed("move_right"):
                    if not self._are_enemies_attached():
                        new_position = self.position + Vector2.RIGHT() * Vector2(
                            delta_time * self.move_speed,
                            delta_time * self.move_speed,
                        )
                        new_position.x = clamp(
                            new_position.x,
                            level_state.boundary.x,
                            level_state.boundary.w,
                        )
                        self.position = new_position
                    else:
                        self._handle_attached_shake(Vector2.RIGHT())
                    self.anim_sprite.flip_h = False
                jump_vector = Vector2(delta_time * jump_speed, delta_time * jump_speed)
                if is_ascending:
                    self.position += Vector2.UP() * jump_vector
                    ascend_timer.tick(delta_time)
                    if ascend_timer.time_remaining <= 0:
                        is_ascending = False
                else:
                    self.position += Vector2.DOWN() * jump_vector
                    descent_timer.tick(delta_time)
                    if descent_timer.time_remaining <= 0:
                        self.stance = PlayerStance.STANDING
                        await co_return()
                await co_suspend()
        except GeneratorExit:
            if attack_task:
                attack_task.close()
