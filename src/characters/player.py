from src.characters.enemy import Enemy, EnemyAttack
from src.characters.player_attack import PlayerMeleeAttack, PlayerSpecialAttack
from src.characters.player_item_handler import PlayerItemHandler
from src.environment.bridge_gate import BridgeGate
from src.items import *
from src.level_state import LevelState
from src.utils.game_math import clamp, Easer, Ease
from src.utils.task import *
from src.utils.timer import Timer


class PlayerStance:
    STANDING = "standing"
    CROUCHING = "crouching"
    IN_AIR = "in_air"


class Player(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.anim_sprite: Optional[AnimatedSprite] = None
        self.collider: Optional[Collider2D] = None
        self.stance = PlayerStance.STANDING
        self.stats = PlayerStats(
            base_hp=10,
            base_energy=20,
            base_move_speed=25,
            base_energy_restored_from_attacks=0.5,
            special_attack_charge_time=5.0,
        )
        self.attack_requested = False
        self.can_do_special_attack = False
        self.reset_special_attack_time = False
        self.energy_attack_cost = 5
        self.is_transformed = False
        self.can_untransform = False
        self.deflect_damage_when_charged = False
        self.enemies_attached_to_left: List[Enemy] = []
        self.enemies_attached_to_right: List[Enemy] = []
        self.last_shake_dir = Vector2.ZERO
        # Used when attacking to delay a frame on contact
        self.enemy_collision_invincible = False
        self.in_attack_damage_cooldown = False
        self.damage_cooldown_time = 2.0
        self.physics_update_task = Task(coroutine=self._physics_update_task())
        self.transformation_task: Optional[Task] = None
        self.health_restore_task: Optional[Task] = None
        self.attack_slash_audio_source = AudioManager.get_audio_source(
            "assets/audio/sfx/attack_slash.wav"
        )
        self.attack_hit_audio_source = AudioManager.get_audio_source(
            "assets/audio/sfx/attack_hit.wav"
        )
        self.collect_item_audio_source = AudioManager.get_audio_source(
            "assets/audio/sfx/collect_item.wav"
        )
        self.pause_game_toggle_audio_source = AudioManager.get_audio_source(
            "assets/audio/sfx/pause_game_toggle.wav"
        )
        self._current_animation_name = ""  # TODO: Add function to engine instead
        self.item_handler: Optional[PlayerItemHandler] = None
        self.input_enabled = True

    def _start(self) -> None:
        self.anim_sprite = self.get_child("AnimatedSprite")
        self.anim_sprite.shader_instance = ShaderUtil.compile_shader(
            "shaders/outline.shader"
        )

        self.collider = self.get_child("Collider2D")
        self.stats.refresh_bar_nodes()
        Camera2D.follow_node(self)

        # Start with 0 energy
        self.stats.energy = 0
        self.item_handler = PlayerItemHandler()

    @staticmethod
    def find_player() -> Optional["Player"]:
        player: Player = SceneTree.get_root().get_child("Player")
        return player

    def _update(self, delta_time: float) -> None:
        if not self.input_enabled:
            return None
        # Pause game
        level_state = LevelState()
        if Input.is_action_just_pressed("start"):
            if not level_state.is_paused:
                World.set_time_dilation(0.0)
            else:
                World.set_time_dilation(1.0)
            level_state.is_paused = not level_state.is_paused
            AudioManager.play_sound(self.pause_game_toggle_audio_source)

        if not self._are_enemies_attached() and not level_state.is_game_state_paused():
            if Input.is_action_just_pressed("attack"):
                hovered_item = self.item_handler.get_hovered_item()
                if hovered_item and hovered_item.can_be_activated(self.stats):
                    self._activate_item(hovered_item)
                else:
                    self.attack_requested = True
            elif Input.is_action_just_pressed("special"):
                if self.is_transformed:
                    if self.can_untransform:
                        self._set_transformed(False)
                        if self.transformation_task:
                            self.transformation_task.close()
                            self.transformation_task = None
                else:
                    min_transform_amount = 2
                    if self.stats.energy >= min_transform_amount:
                        self._set_transformed(True)
                        self.transformation_task = Task(
                            coroutine=self._transformation_task()
                        )

    def _fixed_update(self, delta_time: float) -> None:
        self.physics_update_task.resume()

    def play_animation(self, anim_name: str) -> None:
        self._current_animation_name = anim_name
        if self.is_transformed:
            self.anim_sprite.play(f"{anim_name}_t")
        else:
            self.anim_sprite.play(anim_name)

    def get_current_animation_name(self) -> str:
        return self._current_animation_name

    def _activate_item(self, item: Item) -> None:
        item.on_activation()
        self.item_handler.hide_description()
        if item.can_be_collected:
            item.collect()
            if item.play_collected_sfx:
                AudioManager.play_sound(self.collect_item_audio_source)
            # Item specific
            item_type = type(item)
            if issubclass(item_type, HealthRestoreItem):
                health_item: HealthRestoreItem = item
                self.health_restore_task = Task(
                    coroutine=self._health_restore_task(health_item.restore_amount)
                )
            elif issubclass(item_type, EnergyDrainDecreaseItem):
                self.stats.transformation_energy_drain -= 0.25
            elif issubclass(item_type, DamageDecreaseItem):
                self.stats.damage_taken_from_attacks_multiple -= 0.25
            elif issubclass(item_type, AttackRangeIncreaseItem):
                self.stats.extra_attack_range += 1
            elif issubclass(item_type, SpecialAttackTimeDecreaseItem):
                self.stats.special_attack_charge_time -= 1
            elif issubclass(item_type, DamageDeflectWhenChargedItem):
                self.deflect_damage_when_charged = True

            if item.is_unique:
                self.item_handler.held_unique_items.append(item_type)

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
                    enemy.destroy_from_shake()
            for enemy in self.enemies_attached_to_right[:]:
                enemy.current_attached_shakes += 1
                if enemy.current_attached_shakes >= enemy.shakes_required_for_detach:
                    self.enemies_attached_to_right.remove(enemy)
                    enemy.destroy_from_shake()
            if self._are_enemies_attached():
                self.last_shake_dir = new_shake_dir
            else:
                self.last_shake_dir = Vector2.ZERO

    def _execute_attack(self) -> None:
        flip_h = self.anim_sprite.flip_h
        if flip_h:
            attack_dir = Vector2.LEFT
        else:
            attack_dir = Vector2.RIGHT
        attack_z_index = self.z_index + 1
        if self.can_do_special_attack:
            special_attack = PlayerSpecialAttack.new()
            special_attack.z_index = attack_z_index
            special_attack.direction = attack_dir
            special_attack.flip_h = flip_h
            special_attack.update_attack_offset(
                is_crouching=self.stance == PlayerStance.CROUCHING,
                base_pos=self.position,
            )
            special_attack.subscribe_to_event(
                event_id="hit_enemy",
                scoped_node=self,
                callback_func=lambda enemy: self._on_attack_hit_enemy(enemy),
            )
            SceneTree.get_root().add_child(special_attack)
            self.can_do_special_attack = False
        else:
            melee_attack = PlayerMeleeAttack.new()
            melee_attack.subscribe_to_event(
                event_id="hit_enemy",
                scoped_node=self,
                callback_func=lambda enemy: self._on_attack_hit_enemy(enemy),
            )
            melee_attack.z_index = attack_z_index
            melee_attack.flip_h = flip_h
            melee_attack.update_attack_offset(
                is_crouching=self.stance == PlayerStance.CROUCHING
            )
            if self.is_transformed:
                melee_attack.damage += 1
            self.add_child(melee_attack)
            self.reset_special_attack_time = True
        AudioManager.play_sound(source=self.attack_slash_audio_source)

    def _on_attack_hit_enemy(self, enemy: Enemy) -> None:
        self.stats.set_energy(
            self.stats.energy + self.stats.energy_restored_from_attacks
        )
        if enemy in self.enemies_attached_to_left:
            self.enemies_attached_to_left.remove(enemy)
        elif enemy in self.enemies_attached_to_right:
            self.enemies_attached_to_right.remove(enemy)
        AudioManager.play_sound(source=self.attack_hit_audio_source)

    def _set_transformed(self, is_transformed: bool) -> None:
        if self.is_transformed != is_transformed:
            self.is_transformed = is_transformed
            if self.is_transformed:
                self.stats.move_speed += 5
                self.stats.energy_restored_from_attacks = 0.25
                self.can_untransform = False
            else:
                self.stats.reset_move_speed()
                self.stats.reset_energy_restored_from_attacks()

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
    async def _physics_update_task(self):
        level_state = LevelState()
        collision_task = Task(coroutine=self._collision_check_task())
        manage_special_attack_state_task = Task(
            coroutine=self._manage_special_attack_state_task()
        )
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
                collision_task.resume()
                # Transformation task
                if self.transformation_task:
                    self.transformation_task.resume()
                    if self.stats.energy == 0:
                        self._set_transformed(False)
                        self.transformation_task.close()
                        self.transformation_task = None
                # Health restore task
                if self.health_restore_task:
                    self.health_restore_task.resume()
                # Special attack management task
                manage_special_attack_state_task.resume()
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

    async def _manage_special_attack_state_task(self):
        try:
            level_state = LevelState()
            shader_instance = self.anim_sprite.shader_instance
            charge_timer = Timer(self.stats.special_attack_charge_time)
            while True:
                if self.reset_special_attack_time:
                    charge_timer.time = self.stats.special_attack_charge_time
                    charge_timer.reset()
                    self.reset_special_attack_time = False
                if not level_state.is_currently_transitioning_within_level:
                    charge_timer.tick(self.get_full_time_dilation_with_physics_delta())
                if charge_timer.has_stopped():
                    self.can_do_special_attack = True
                    shader_instance.set_float_param("outline_width", 1.4)
                    await co_suspend()
                    shader_instance.set_float_param("outline_width", 1.2)
                    await co_suspend()
                    shader_instance.set_float_param("outline_width", 1.0)
                    await co_suspend()
                    charged_outline_width = 0.7
                    while (
                        self.can_do_special_attack
                        and not self.reset_special_attack_time
                    ):
                        if World.get_time_dilation() > 0.0:
                            shader_instance.set_float_param(
                                "outline_width", charged_outline_width
                            )
                            if charged_outline_width == 0.7:
                                charged_outline_width = 0.8
                            elif charged_outline_width == 0.8:
                                charged_outline_width = 0.9
                            else:
                                charged_outline_width = 0.7
                        await co_suspend()
                    shader_instance.set_float_param("outline_width", 0.0)
                    charge_timer.time = self.stats.special_attack_charge_time
                    charge_timer.reset()
                    self.reset_special_attack_time = False
                await co_suspend()
        except GeneratorExit:
            pass

    async def _damage_cooldown_task(
        self,
        cooldown_time: Optional[float] = None,
        gamepad_vibration=True,
        hp_damage=1.0,
        modulate_color=True,
    ):
        if not cooldown_time:
            cooldown_time = self.damage_cooldown_time
        take_transform_damage = self.is_transformed
        if take_transform_damage:
            bar_ui = self.stats.energy_bar_ui
        else:
            bar_ui = self.stats.health_bar_ui

        def subtract_hp_value(damage: float, bar_color: Color) -> None:
            if not self.can_do_special_attack or (
                self.can_do_special_attack and not self.deflect_damage_when_charged
            ):
                damage *= self.stats.damage_taken_from_attacks_multiple
                if take_transform_damage:
                    self.stats.energy -= damage
                else:
                    self.stats.hp -= damage
            bar_ui.color = bar_color
            self.can_do_special_attack = False

        normal_hp_bar_color = bar_ui.color
        try:
            if gamepad_vibration:
                Input.start_gamepad_vibration(0, 0.5, 0.5, 0.25)
            cooldown_timer = Timer(cooldown_time)
            has_subtracted_health = False
            is_game_over = False
            bar_ui.color = Color(240, 247, 243)
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
                        if self.stats.hp <= 0.0:
                            is_game_over = True
                            break
                    await co_suspend()
                else:
                    if modulate_color:
                        self.anim_sprite.modulate = Color(255, 255, 255, 255)
                    if not has_subtracted_health:
                        subtract_hp_value(hp_damage, normal_hp_bar_color)
                        if self.stats.hp <= 0.0:
                            is_game_over = True
                    break
            if is_game_over:
                self.input_enabled = False
                # Stop Music
                main_theme_audio_source = AudioManager.get_audio_source(
                    "assets/audio/music/main_theme.wav"
                )
                AudioManager.stop_sound(source=main_theme_audio_source)
                boss_theme_audio_source = AudioManager.get_audio_source(
                    "assets/audio/music/boss_theme.wav"
                )
                AudioManager.stop_sound(source=boss_theme_audio_source)
                # Stop time dilation and beam player up
                World.set_time_dilation(0.0)
                await Task(coroutine=self._beam_player_up())
                await Task(
                    coroutine=LevelState.fade_transition(time=1.0, fade_out=True)
                )
                SceneTree.change_scene("scenes/end_game_screen.cscn")
                World.set_time_dilation(1.0)
        except GeneratorExit:
            bar_ui.color = normal_hp_bar_color

    async def _collision_check_task(self):
        try:
            damage_cooldown_task: Optional[Task] = None
            attached_damage_cooldown_task: Optional[Task] = None
            level_state = LevelState()
            player_hurt_audio_source = AudioManager.get_audio_source(
                "assets/audio/sfx/player_hurt.wav"
            )
            while True:
                collisions = CollisionHandler.process_collisions(self.collider)
                show_item_description = False
                for collider in collisions:
                    collider_parent = collider.get_parent()
                    collider_parent_type = type(collider_parent)
                    if collider_parent.is_queued_for_deletion:
                        continue
                    # Enemy Collision
                    if (
                        issubclass(collider_parent_type, Enemy)
                        and not self.enemy_collision_invincible
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
                                collider_parent.destroy_from_contact()
                            self.in_attack_damage_cooldown = True
                            AudioManager.play_sound(player_hurt_audio_source)
                            damage_cooldown_task = Task(
                                coroutine=self._damage_cooldown_task()
                            )
                    # Enemy Attack Collision
                    elif (
                        issubclass(collider_parent_type, EnemyAttack)
                        and not self.enemy_collision_invincible
                        and not self.in_attack_damage_cooldown
                    ):
                        collider_parent.queue_deletion()
                        self.in_attack_damage_cooldown = True
                        AudioManager.play_sound(player_hurt_audio_source)
                        damage_cooldown_task = Task(
                            coroutine=self._damage_cooldown_task()
                        )
                    # Power Up
                    elif issubclass(collider_parent_type, Item):
                        self.item_handler.show_description(collider_parent)
                        show_item_description = True
                    elif issubclass(collider_parent_type, BridgeGate):
                        bridge_gate: BridgeGate = collider_parent
                        if (
                            bridge_gate.is_opened
                            and not bridge_gate.has_player_ever_stepped_through
                        ):
                            bridge_gate.has_player_ever_stepped_through = True
                            level_state.queue_gate_transition()
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
                if not show_item_description:
                    self.item_handler.hide_description()
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
            level_state = LevelState()
            transformation_tick_rate = 0.25
            energy_drain_per_tick = self.stats.transformation_energy_drain
            # Update animation to transformed
            self.play_animation(self._current_animation_name)
            times_ticked = 0
            while True:
                await co_wait_seconds(transformation_tick_rate)
                if not level_state.is_currently_transitioning_within_level:
                    self.stats.energy -= energy_drain_per_tick
                    times_ticked += 1
                    if times_ticked == 2:
                        self.can_untransform = True
                await co_suspend()
        except GeneratorExit:
            self.play_animation(self._current_animation_name)
            self.can_untransform = True

    async def _health_restore_task(self, restore_amount: int):
        try:
            self.input_enabled = False
            World.set_time_dilation(0.0)
            health_gain_audio_source = AudioManager.get_audio_source(
                "assets/audio/sfx/health_gain.wav"
            )
            amount_to_restore = restore_amount
            while self.stats.hp < self.stats.base_hp and amount_to_restore > 0:
                self.stats.hp += 1
                AudioManager.play_sound(health_gain_audio_source)
                amount_to_restore -= 1
                await co_suspend()
                await co_suspend()
            self.input_enabled = True
            World.set_time_dilation(1.0)
        except GeneratorExit:
            pass

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
                    continue
                elif self.input_enabled:
                    if Input.is_action_pressed("move_left"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.LEFT * Vector2(
                                delta_time * self.stats.move_speed,
                                delta_time * self.stats.move_speed,
                            )
                            new_position = self._get_clamped_pos(
                                new_position, level_state.boundary
                            )
                            self.play_animation("walk")
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.LEFT)
                        self.anim_sprite.flip_h = True
                    elif Input.is_action_pressed("move_right"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.RIGHT * Vector2(
                                delta_time * self.stats.move_speed,
                                delta_time * self.stats.move_speed,
                            )
                            new_position = self._get_clamped_pos(
                                new_position, level_state.boundary
                            )
                            self.play_animation("walk")
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.RIGHT)
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
                    continue
                elif self.input_enabled:
                    if Input.is_action_pressed("move_left"):
                        if self._are_enemies_attached():
                            self._handle_attached_shake(Vector2.LEFT)
                        self.anim_sprite.flip_h = True
                    elif Input.is_action_pressed("move_right"):
                        if self._are_enemies_attached():
                            self._handle_attached_shake(Vector2.RIGHT)
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
        current_jump_anim = "jump_up"
        self.play_animation(current_jump_anim)
        attack_task: Optional[Task] = None
        try:
            level_state = LevelState()
            jump_speed = 30
            jump_time = 0.5
            ascend_timer = Timer(jump_time)
            max_ascend_timer_skips = 2
            if self.is_transformed:
                max_ascend_timer_skips += 2
            ascent_timer_skips = 0
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
                        self.play_animation(current_jump_anim)
                if self.input_enabled:
                    if Input.is_action_pressed("move_left"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.LEFT * Vector2(
                                delta_time * self.stats.move_speed,
                                delta_time * self.stats.move_speed,
                            )
                            new_position = self._get_clamped_pos(
                                new_position, level_state.boundary
                            )
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.LEFT)
                        self.anim_sprite.flip_h = True
                    elif Input.is_action_pressed("move_right"):
                        if not self._are_enemies_attached():
                            new_position = self.position + Vector2.RIGHT * Vector2(
                                delta_time * self.stats.move_speed,
                                delta_time * self.stats.move_speed,
                            )
                            new_position = self._get_clamped_pos(
                                new_position, level_state.boundary
                            )
                            self.position = new_position
                        else:
                            self._handle_attached_shake(Vector2.RIGHT)
                        self.anim_sprite.flip_h = False
                jump_vector = Vector2(delta_time * jump_speed, delta_time * jump_speed)
                if is_ascending:
                    self.position += Vector2.UP * jump_vector
                    skip_ascend_timer = (
                        self.input_enabled
                        and Input.is_action_pressed("jump")
                        and ascent_timer_skips < max_ascend_timer_skips
                    )
                    if skip_ascend_timer:
                        ascent_timer_skips += 1
                    else:
                        ascend_timer.tick(delta_time)
                    if ascend_timer.time_remaining <= 0:
                        is_ascending = False
                        current_jump_anim = "jump_down"
                        if not attack_task:
                            self.play_animation(current_jump_anim)
                else:
                    self.position += Vector2.DOWN * jump_vector
                    if self.position.y == level_state.floor_y:
                        self.stance = PlayerStance.STANDING
                        await co_return()
                await co_suspend()
        except GeneratorExit:
            if attack_task:
                attack_task.close()

    async def _beam_player_up(self):
        try:
            player_initial_pos = self.position + Vector2(0, -8)
            player_dest_pos = Vector2(player_initial_pos.x, -20)
            player_teleport_beam: Sprite = Sprite.new()
            player_teleport_beam.position = player_initial_pos
            player_teleport_beam.texture = Texture(
                file_path="assets/images/demi/demi_teleport.png"
            )
            player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
            player_teleport_beam.origin = Vector2(25, 18)
            player_teleport_beam.z_index = 10
            SceneTree.get_root().add_child(player_teleport_beam)
            player_beam_timer = Timer(3.0)
            player_beam_easer = Easer(
                player_initial_pos,
                player_dest_pos,
                player_beam_timer.time,
                Ease.Cubic.ease_in_vec2,
            )

            self.anim_sprite.modulate = Color(255, 255, 255, 0)

            # Hard code animation that delays 2 frames each
            player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
            await co_suspend()
            await co_suspend()
            player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
            await co_suspend()
            await co_suspend()
            player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
            await co_suspend()
            await co_suspend()
            player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
            await co_suspend()
            await co_suspend()
            player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
            await co_suspend()
            await co_suspend()

            while True:
                delta_time = Engine.get_global_physics_delta_time()
                player_beam_timer.tick(delta_time)
                if player_beam_timer.time_remaining > 0.0:
                    new_beam_pos = player_beam_easer.ease(delta_time)
                    player_teleport_beam.position = new_beam_pos
                    await co_suspend()
                else:
                    player_teleport_beam.queue_deletion()
                    break
        except GeneratorExit:
            pass
