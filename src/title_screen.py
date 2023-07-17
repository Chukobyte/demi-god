from crescent_api import *

from src.level_state import LevelState
from src.option_box_manager import OptionBoxManager
from src.utils.game_math import Easer, Ease
from src.utils.task import Task, co_suspend, co_wait_seconds
from src.utils.timer import Timer


class TitleScreen(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.update_task = Task(coroutine=self._update_task())
        self.option_box_manager: Optional[OptionBoxManager] = None
        self.title_sprite: Optional[Sprite] = None
        self.option_box_sprite: Optional[Sprite] = None
        self.option_arrow_top_sprite: Optional[Sprite] = None
        self.option_arrow_bottom_sprite: Optional[Sprite] = None
        self.option_text_label: Optional[TextLabel] = None
        self.copyright_sprite: Optional[Sprite] = None
        self.buildings_sprite: Optional[Sprite] = None
        self.white_rect: Optional[ColorRect] = None
        self.title_screen_anims_finished = False
        self.skip_title_screen_anims = False
        self.confirmed_option: Optional[str] = None

    def _start(self) -> None:
        LevelState.reset_instance()
        level_state = LevelState()
        if not level_state.screen_shader_instance:
            level_state.screen_shader_instance = ShaderUtil.compile_shader(
                shader_path="shaders/screen.shader"
            )
        ShaderUtil.set_screen_shader(shader_instance=level_state.screen_shader_instance)
        level_state.screen_shader_instance.set_float_param("brightness", 0.0)
        self.title_sprite = self.get_child("Title")
        new_title_pos = self.title_sprite.position
        new_title_pos.y -= 100
        self.title_sprite.position = new_title_pos
        self.option_box_sprite = self.get_child("OptionBox")
        self.option_box_sprite.modulate = Color(255, 255, 255, 0)
        self.option_arrow_top_sprite: Sprite = self.get_child("OptionArrowTop")
        self.option_arrow_top_sprite.modulate = Color(255, 255, 255, 0)
        self.option_arrow_bottom_sprite: Sprite = self.get_child("OptionArrowBot")
        self.option_arrow_bottom_sprite.modulate = Color(255, 255, 255, 0)
        self.option_text_label: TextLabel = self.get_child("OptionsTextLabel")
        self.option_text_label.color = Color(2, 3, 2, 0)
        self.copyright_sprite = self.get_child("Copyright")
        self.copyright_sprite.modulate = Color(255, 255, 255, 0)
        self.buildings_sprite = self.get_child("Buildings")
        self.white_rect = self.get_child("WhiteRect")

        self.option_box_manager = OptionBoxManager(
            self.option_text_label,
            self.option_arrow_bottom_sprite,
            self.option_arrow_top_sprite,
            ["Start", "Exit"],
        )

    def _update(self, delta_time: float) -> None:
        if Input.is_action_just_pressed("ui_confirm"):
            if self.title_screen_anims_finished:
                self.confirmed_option = self.option_box_manager.get_selected_option()
                self.option_box_manager.is_enabled = False
            else:
                self.skip_title_screen_anims = True

        if self.title_screen_anims_finished:
            self.option_box_manager.process_inputs()

    def _fixed_update(self, delta_time: float) -> None:
        self.update_task.resume()
        self.option_box_manager.update_tasks()

    # --- TASKS --- #
    async def _update_task(self):
        try:
            await Task(coroutine=LevelState.fade_transition(time=1.0, fade_out=False))

            time_for_title_to_move_to_pos = 5.0
            title_easer = Easer(
                self.title_sprite.position,
                Vector2.ZERO,
                time_for_title_to_move_to_pos,
                Ease.Cubic.ease_out_vec2,
            )
            title_screen_done_timer = Timer(time_for_title_to_move_to_pos)
            ease_ui_task = Task(coroutine=self._ease_ui_task())
            while not self.confirmed_option:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                # Title
                if self.skip_title_screen_anims:
                    self.title_sprite.position = Vector2.ZERO
                    title_screen_done_timer.time_remaining = 0.0
                else:
                    self.title_sprite.position = title_easer.ease(delta_time)
                title_screen_done_timer.tick(delta_time)
                if title_screen_done_timer.time_remaining <= 0.0:
                    self.title_screen_anims_finished = True
                    # Press Start
                    ease_ui_task.resume()
                await co_suspend()
            selected_option = self.confirmed_option
            if selected_option == "Start":
                # Go to game now
                self.option_box_sprite.modulate = Color(255, 255, 255)
                self.option_arrow_top_sprite.modulate = Color(255, 255, 255)
                self.option_arrow_bottom_sprite.modulate = Color(255, 255, 255)
                self.option_text_label.color = Color(2, 3, 2, 255)
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
                await Task(
                    coroutine=LevelState.fade_transition(time=1.0, fade_out=True)
                )
                SceneTree.change_scene("scenes/main.cscn")
            elif selected_option == "Exit":
                await Task(
                    coroutine=LevelState.fade_transition(time=1.0, fade_out=True)
                )
                Engine.exit()
        except GeneratorExit:
            pass

    async def _ease_ui_task(self):
        try:
            # Ease in appearance
            appearance_easer = Easer(0, 255, 1.0, Ease.Cubic.ease_out)
            while True:
                delta_time = self.get_full_time_dilation_with_physics_delta()
                new_alpha = int(appearance_easer.ease(delta_time))
                self.option_box_sprite.modulate = Color(255, 255, 255, new_alpha)
                self.option_arrow_top_sprite.modulate = Color(255, 255, 255, new_alpha)
                self.option_arrow_bottom_sprite.modulate = Color(
                    255, 255, 255, new_alpha
                )
                self.option_text_label.color = Color(2, 3, 2, new_alpha)
                self.copyright_sprite.modulate = Color(255, 255, 255, new_alpha)
                if new_alpha == 255:
                    break
                await co_suspend()

            self.option_box_sprite.modulate = Color(255, 255, 255)
            self.option_arrow_top_sprite.modulate = Color(255, 255, 255)
            self.option_arrow_bottom_sprite.modulate = Color(255, 255, 255)
            self.option_text_label.color = Color(2, 3, 2, 255)
            self.copyright_sprite.modulate = Color(255, 255, 255)
        except GeneratorExit:
            pass
