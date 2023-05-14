import random

from crescent_api import *

from src.characters.player import Player
from src.characters.wandering_soul import WanderingSoul
from src.enemy_manager import EnemyManager
from src.level_clouds import LevelCloudManager
from src.level_state import LevelState
from src.environment.bridge_gate import BridgeGate
from src.utils.game_math import Ease, Easer
from src.utils.task import *
from src.utils.timer import Timer


class SpawnedCloud(Sprite):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.move_speed = random.randint(5, 15)
        self.move_dir = Vector2.RIGHT()
        self._elapsed_time = 0.0

    def _fixed_update(self, delta_time: float) -> None:
        self._elapsed_time += delta_time
        current_pos = self.position
        new_pos = (
            current_pos
            + Vector2(delta_time * self.move_speed, delta_time * self.move_speed)
            * self.move_dir
        )
        self.position = Ease.Cubic.ease_in_vec2(
            elapsed_time=self._elapsed_time,
            from_pos=current_pos,
            to_pos=new_pos,
            duration=self._elapsed_time + 0.1,
        )


class GameMaster:
    # Manages game state such as enemy spawning
    def __init__(self, main_node):
        self.main = main_node
        self.player: Optional[Player] = None
        self.spawned_clouds: List[SpawnedCloud] = []
        self.main_task = Task(coroutine=self._update_task())
        self.bridge_transition_task: Optional[Task] = None

    def update(self) -> None:
        self.main_task.resume()

    # --- TASKS --- #
    async def _update_task(self):
        player_start_pos = Vector2(20, 78)
        enemy_waves_task: Optional[Task] = None
        level_cloud_manager = LevelCloudManager()
        try:
            # TODO: put in main.py
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))

            # TODO: Place in a place when the game ends instead
            LevelState.reset_instance()
            level_state = LevelState()
            Camera2D.set_boundary(level_state.boundary)

            # Spawn bridge gate TODO: Move another place
            bridge_gate = BridgeGate.new()
            bridge_gate.position = Vector2(
                level_state.boundary.w - 10, level_state.floor_y - 31
            )
            bridge_gate.z_index = 2
            self.main.add_child(bridge_gate)

            # Shoot down player beam first
            player_teleport_beam = Sprite.new()
            player_teleport_beam.texture = Texture(
                file_path="assets/images/demi/demi_teleport.png"
            )
            player_teleport_beam.draw_source = Rect2(0, 0, 48, 48)
            player_teleport_beam.origin = Vector2(25, 18)
            player_teleport_beam.z_index = 3
            self.main.add_child(player_teleport_beam)
            player_beam_timer = Timer(3.0)
            player_beam_easer = Easer(
                Vector2(player_start_pos.x, -20),
                player_start_pos,
                player_beam_timer.time,
                Ease.Cubic.ease_in_vec2,
            )
            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                player_beam_timer.tick(delta_time)
                level_cloud_manager.update()
                if player_beam_timer.time_remaining > 0.0:
                    new_beam_pos = player_beam_easer.ease(delta_time)
                    player_teleport_beam.position = new_beam_pos
                    await co_suspend()
                else:
                    # Hard code animation that delays 2 frames each
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
                    player_teleport_beam.draw_source = Rect2(48, 0, 48, 48)
                    await co_suspend()
                    await co_suspend()
                    player_teleport_beam.queue_deletion()
                    break

            main_theme_audio_source = AudioManager.get_audio_source(
                "assets/audio/music/main_theme.wav"
            )
            AudioManager.play_sound(source=main_theme_audio_source, loops=True)

            player_scene = SceneUtil.load_scene("scenes/characters/player.cscn")
            self.player: Player = player_scene.create_instance()
            self.player.position = player_start_pos
            self.main.add_child(self.player)

            enemy_manager = EnemyManager(main=self.main, player=self.player)
            enemy_waves_task = Task(coroutine=enemy_manager.enemy_waves_task())

            while True:
                if level_state.is_gate_transition_queued:
                    if self.bridge_transition_task:
                        self.bridge_transition_task.close()
                    self.bridge_transition_task = Task(
                        coroutine=self._manage_bridge_transition_task(
                            level_cloud_manager
                        )
                    )
                    level_state.is_gate_transition_queued = False
                if self.bridge_transition_task:
                    self.bridge_transition_task.resume()
                enemy_waves_task.resume()
                level_cloud_manager.update()
                await co_suspend()
        except GeneratorExit:
            if enemy_waves_task:
                enemy_waves_task.close()

    async def _manage_bridge_transition_task(
        self, level_cloud_manager: LevelCloudManager
    ):
        try:
            level_state = LevelState()
            prev_player_time_dilation = self.player.time_dilation
            self.player.time_dilation = 0.0
            level_cloud_manager.set_clouds_time_dilation(0.0)
            level_state.boundary.w += 160
            Camera2D.unfollow_node(self.player)
            Camera2D.set_boundary(level_state.boundary)
            transition_timer = Timer(5.0)
            initial_camera_pos = Camera2D.get_position()
            dest_camera_pos = Vector2(
                level_state.boundary.w - 160, initial_camera_pos.y
            )
            camera_pos_easer = Easer(
                initial_camera_pos,
                dest_camera_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            initial_player_pos = self.player.position
            player_dest_pos = initial_player_pos + Vector2(30, 0)
            player_pos_easer = Easer(
                initial_player_pos,
                player_dest_pos,
                transition_timer.time,
                Ease.Cubic.ease_out_vec2,
            )

            await co_wait_seconds(1.0)
            self.player.time_dilation = prev_player_time_dilation
            self.player.play_animation("walk")
            level_cloud_manager.set_clouds_time_dilation(1.0)

            while True:
                delta_time = (
                    Engine.get_global_physics_delta_time() * World.get_time_dilation()
                )
                transition_timer.tick(delta_time)
                if transition_timer.time_remaining <= 0.0:
                    Camera2D.set_position(dest_camera_pos)
                    self.player.position = player_dest_pos
                    break
                else:
                    new_camera_pos = camera_pos_easer.ease(delta_time)
                    Camera2D.set_position(new_camera_pos)
                    new_player_pos = player_pos_easer.ease(delta_time)
                    self.player.position = new_player_pos
                await co_suspend()
            level_state.boundary.x = level_state.boundary.w - 160
            Camera2D.set_boundary(level_state.boundary)
            Camera2D.follow_node(self.player)
            bridge_gate: BridgeGate = self.main.get_child("Sprite")  # temp
            if bridge_gate:
                bridge_gate.set_closed()
            level_state.is_currently_transitioning_within_level = False
            # Temp wandering soul spawn
            wandering_soul = WanderingSoul.new()
            wandering_soul.position = Vector2(
                level_state.boundary.w - 32, level_state.floor_y
            )
            wandering_soul.z_index = 10
            self.main.add_child(wandering_soul)
        except GeneratorExit:
            pass

    async def _manage_clouds_task(self):
        try:
            max_clouds = 10
            cloud_textures = [
                Texture(file_path="assets/images/environment/cloud_variation1.png"),
                Texture(file_path="assets/images/environment/cloud_variation2.png"),
                Texture(file_path="assets/images/environment/cloud_variation3.png"),
                Texture(file_path="assets/images/environment/cloud_variation4.png"),
            ]
            cloud_texture_draw_source = Rect2(0, 0, 32, 18)
            self.spawned_clouds.clear()
            # Spawn initial clouds
            clouds_to_spawn = max_clouds - len(self.spawned_clouds)
            camera_pos = Camera2D.get_position()
            for i in range(clouds_to_spawn):
                cloud = SpawnedCloud.new()
                cloud.texture = random.choice(cloud_textures)
                cloud.draw_source = cloud_texture_draw_source
                cloud.position = camera_pos + Vector2(
                    i * random.randint(5, 40), random.randint(0, 40)
                )
                cloud.z_index = 2
                self.spawned_clouds.append(cloud)
                self.main.add_child(cloud)
            while True:
                clouds_to_spawn = max_clouds - len(self.spawned_clouds)
                camera_pos = Camera2D.get_position()
                for i in range(clouds_to_spawn):
                    cloud = SpawnedCloud.new()
                    cloud.texture = random.choice(cloud_textures)
                    cloud.draw_source = cloud_texture_draw_source
                    cloud.position = camera_pos + Vector2(
                        i * random.randint(5, 40), random.randint(0, 40)
                    )
                    cloud.z_index = 2
                    self.spawned_clouds.append(cloud)
                    self.main.add_child(cloud)
                await co_wait_seconds(10.0)
        except GeneratorExit:
            pass
