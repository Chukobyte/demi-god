import random
from typing import Tuple

from crescent_api import *
from crescent_api import Vector2

from src.utils.game_math import Ease
from src.utils.task import co_wait_seconds, Task


CLOUD_TEXTURES = [
    Texture(file_path="assets/images/environment/cloud_variation1.png"),
    Texture(file_path="assets/images/environment/cloud_variation2.png"),
    Texture(file_path="assets/images/environment/cloud_variation3.png"),
    Texture(file_path="assets/images/environment/cloud_variation4.png"),
]


class LevelCloud(Sprite):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.move_speed = random.randint(5, 15)
        self.move_dir = Vector2.RIGHT
        self._elapsed_time = 0.0

    def set_random_texture(self) -> None:
        self.texture = random.choice(CLOUD_TEXTURES)

    def _fixed_update(self, delta_time: float) -> None:
        self._elapsed_time += delta_time
        current_pos = self.position
        new_pos = (
            current_pos
            + Vector2(delta_time * self.move_speed, delta_time * self.move_speed)
            * self.move_dir
        )
        new_pos = Ease.Cubic.ease_in_vec2(
            elapsed_time=self._elapsed_time,
            from_pos=current_pos,
            to_pos=new_pos,
            duration=self._elapsed_time + 0.1,
        )
        new_pos, has_repositioned = self._attempt_reposition(new_pos)
        self.position = new_pos
        # Set random texture when repositioned
        if has_repositioned:
            self.set_random_texture()

    def _attempt_reposition(
        self, position: Vector2, padding=96
    ) -> tuple[Vector2, bool]:
        camera_pos = Camera2D.get_position()
        game_props = GameProperties()
        camera_dimension = Size2D(
            game_props.game_resolution.w + camera_pos.x,
            game_props.game_resolution.h + camera_pos.y,
        )
        # Check if too far to left
        has_repositioned = False
        if position.x < camera_pos.x - padding:
            position.x = camera_dimension.w + padding - 32
            has_repositioned = True
        elif position.x > camera_dimension.w + padding:
            position.x = camera_pos.x - padding + 32
            has_repositioned = True
        return position, has_repositioned


class LevelCloudManager:
    def __init__(self):
        self.manage_clouds_task_handle = Task(coroutine=self._manage_clouds_task())
        self.spawned_clouds: List[LevelCloud] = []

    def update(self) -> None:
        self.manage_clouds_task_handle.resume()

    async def _manage_clouds_task(self):
        try:
            max_clouds = 10
            cloud_texture_draw_source = Rect2(0, 0, 32, 18)
            self.spawned_clouds.clear()
            # Spawn initial clouds
            clouds_to_spawn = max_clouds - len(self.spawned_clouds)
            camera_pos = Camera2D.get_position()
            main_node = SceneTree.get_root()
            for i in range(clouds_to_spawn):
                cloud = LevelCloud.new()
                cloud.set_random_texture()
                cloud.draw_source = cloud_texture_draw_source
                cloud.position = camera_pos + Vector2(
                    i * random.randint(5, 40), random.randint(0, 40)
                )
                cloud.z_index = 1
                self.spawned_clouds.append(cloud)
                main_node.add_child(cloud)
            while True:
                clouds_to_spawn = max_clouds - len(self.spawned_clouds)
                camera_pos = Camera2D.get_position()
                for i in range(clouds_to_spawn):
                    cloud = LevelCloud.new()
                    cloud.set_random_texture()
                    cloud.draw_source = cloud_texture_draw_source
                    cloud.position = camera_pos + Vector2(
                        i * random.randint(5, 40), random.randint(0, 40)
                    )
                    cloud.z_index = 1
                    self.spawned_clouds.append(cloud)
                    main_node.add_child(cloud)
                await co_wait_seconds(10.0)
        except GeneratorExit:
            pass
