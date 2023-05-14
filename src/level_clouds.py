import random

from crescent_api import *

from src.utils.game_math import Ease
from src.utils.task import co_wait_seconds, Task


class LevelCloud(Sprite):
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


class LevelCloudManager:
    def __init__(self):
        self.manage_clouds_task_handle = Task(coroutine=self._manage_clouds_task())
        self.spawned_clouds: List[LevelCloud] = []

    def update(self) -> None:
        self.manage_clouds_task_handle.resume()

    def set_clouds_time_dilation(self, dilation: float) -> None:
        for cloud in self.spawned_clouds:
            cloud.time_dilation = dilation

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
            main_node = SceneTree.get_root()
            for i in range(clouds_to_spawn):
                cloud = LevelCloud.new()
                cloud.texture = random.choice(cloud_textures)
                cloud.draw_source = cloud_texture_draw_source
                cloud.position = camera_pos + Vector2(
                    i * random.randint(5, 40), random.randint(0, 40)
                )
                cloud.z_index = 2
                self.spawned_clouds.append(cloud)
                main_node.add_child(cloud)
            while True:
                clouds_to_spawn = max_clouds - len(self.spawned_clouds)
                camera_pos = Camera2D.get_position()
                for i in range(clouds_to_spawn):
                    cloud = LevelCloud.new()
                    cloud.texture = random.choice(cloud_textures)
                    cloud.draw_source = cloud_texture_draw_source
                    cloud.position = camera_pos + Vector2(
                        i * random.randint(5, 40), random.randint(0, 40)
                    )
                    cloud.z_index = 2
                    self.spawned_clouds.append(cloud)
                    main_node.add_child(cloud)
                await co_wait_seconds(10.0)
        except GeneratorExit:
            pass
