from crescent_api import *

from src.level_state import LevelState
from src.utils.game_math import Easer, Ease
from src.utils.task import Task, co_suspend, co_wait_seconds
from src.utils.timer import Timer


class TitleScreen(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.update_task = Task(coroutine=self._update_task())
        self.title_sprite: Optional[Sprite] = None
        self.press_start_sprite: Optional[Sprite] = None
        self.copyright_sprite: Optional[Sprite] = None
        self.buildings_sprite: Optional[Sprite] = None
        self.white_rect: Optional[ColorRect] = None
        self.title_screen_anims_finished = False
        self.skip_title_screen_anims = False
        self.start_game_triggered = False

    def _start(self) -> None:
        level_state = LevelState()
        if not level_state.screen_shader_instance:
            level_state.screen_shader_instance = ShaderUtil.compile_shader(
                shader_path="shaders/screen.shader"
            )
        ShaderUtil.set_screen_shader(shader_instance=level_state.screen_shader_instance)
        self.title_sprite = self.get_child("Title")
        new_title_pos = self.title_sprite.position
        new_title_pos.y -= 100
        self.title_sprite.position = new_title_pos
        self.press_start_sprite = self.get_child("Press Start")
        self.press_start_sprite.modulate = Color(255, 255, 255, 0)
        self.copyright_sprite = self.get_child("Copyright")
        self.copyright_sprite.modulate = Color(255, 255, 255, 0)
        self.buildings_sprite = self.get_child("Buildings")
        self.white_rect = self.get_child("WhiteRect")

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("exit"):
            Engine.exit()

        if Input.is_action_just_pressed("start"):
            if self.title_screen_anims_finished:
                self.start_game_triggered = True
            else:
                self.skip_title_screen_anims = True

    def _fixed_update(self, delta_time: float) -> None:
        self.update_task.resume()

    # --- TASKS --- #
    async def _update_task(self):
        try:
            time_for_title_to_move_to_pos = 5.0
            title_easer = Easer(
                self.title_sprite.position,
                Vector2.ZERO(),
                time_for_title_to_move_to_pos,
                Ease.Cubic.ease_out_vec2,
            )
            title_screen_done_timer = Timer(time_for_title_to_move_to_pos)
            press_start_flicker_task = Task(coroutine=self._press_start_flicker_task())
            while not self.start_game_triggered:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                # Title
                if self.skip_title_screen_anims:
                    self.title_sprite.position = Vector2.ZERO()
                    title_screen_done_timer.time_remaining = 0.0
                else:
                    self.title_sprite.position = title_easer.ease(delta_time)
                title_screen_done_timer.tick(delta_time)
                if title_screen_done_timer.time_remaining <= 0.0:
                    self.title_screen_anims_finished = True
                    # Press Start
                    press_start_flicker_task.resume()
                await co_suspend()
            # Go to game now
            self.press_start_sprite.modulate = Color(255, 255, 255)
            self.copyright_sprite.modulate = Color(255, 255, 255)
            start_game_sfx = AudioManager.get_audio_source(
                "assets/audio/sfx/start_game.wav"
            )
            AudioManager.play_sound(start_game_sfx)
            white_rect_visible_alpha = 150
            white_rect_color = self.white_rect.color
            white_rect_color.a = white_rect_visible_alpha
            self.white_rect.color = white_rect_color
            await co_suspend()
            white_rect_color.a = 0
            self.white_rect.color = white_rect_color
            await co_suspend()
            white_rect_color.a = white_rect_visible_alpha
            self.white_rect.color = white_rect_color
            await co_suspend()
            white_rect_color.a = 0
            self.white_rect.color = white_rect_color
            await co_suspend()
            white_rect_color.a = white_rect_visible_alpha
            self.white_rect.color = white_rect_color
            await co_suspend()
            white_rect_color.a = 0
            self.white_rect.color = white_rect_color
            await co_wait_seconds(0.8)
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=True))
            SceneTree.change_scene("scenes/main.cscn")
        except GeneratorExit:
            pass

    async def _press_start_flicker_task(self):
        try:
            # Ease in appearance
            appearance_easer = Easer(0, 255, 1.0, Ease.Cubic.ease_out)
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                new_alpha = int(appearance_easer.ease(delta_time))
                self.press_start_sprite.modulate = Color(255, 255, 255, new_alpha)
                self.copyright_sprite.modulate = Color(255, 255, 255, new_alpha)
                if new_alpha == 255:
                    break
                await co_suspend()

            self.press_start_sprite.modulate = Color(255, 255, 255)
            self.copyright_sprite.modulate = Color(255, 255, 255)
            press_start_timer = Timer(1.0)
            press_start_visible = True
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                press_start_timer.tick(delta_time)
                if press_start_timer.time_remaining <= 0.0:
                    press_start_timer.reset()
                    if press_start_visible:
                        self.press_start_sprite.modulate = Color(255, 255, 255)
                    else:
                        self.press_start_sprite.modulate = Color(255, 255, 255, 0)
                    press_start_visible = not press_start_visible
                await co_suspend()
        except GeneratorExit:
            pass
