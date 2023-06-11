from typing import Optional, List

from crescent_api import *

from src.environment.bridge_gate import BridgeGate
from src.utils.task import co_suspend


class BridgeGateHelper:
    def __init__(self, max_bridges=4):
        self.max_bridges = max_bridges
        self._bridge_gates: List[BridgeGate] = []
        self._current_gate_index = 0

    def spawn_bridge_gates(self) -> None:
        bridges_to_spawn = self.max_bridges - len(self._bridge_gates)
        for i in range(bridges_to_spawn):
            bridge_gate = BridgeGate.new()
            bridge_gate.position = Vector2(-200, -200)
            bridge_gate.z_index = 2
            SceneTree.get_root().add_child(bridge_gate)
            self._bridge_gates.append(bridge_gate)

    def next_bridge_gate(self) -> BridgeGate:
        """
        Increments the bridge gate index and returns the next one
        """
        self._current_gate_index += 1
        if self._current_gate_index > self.max_bridges - 1:
            self._current_gate_index = 0
        return self._bridge_gates[self._current_gate_index]

    def get_current_bridge_gate(self) -> BridgeGate:
        """
        Gets the current BridgeGate, basically the last one that was used
        """
        return self._bridge_gates[self._current_gate_index]

    def get_previous_bridge_gate(self) -> BridgeGate:
        """
        Just get the previous bridge gate (without decrementing)
        """
        prev_gate_index = self._current_gate_index - 1
        if prev_gate_index < 0:
            prev_gate_index = self.max_bridges - 1
        return self._bridge_gates[prev_gate_index]


class GameTimer:
    def __init__(self, time_label: TextLabel):
        self.time_label = time_label
        self._time = 0.0

    def get_formatted_time(self) -> str:
        time_seconds = int(self._time)
        if time_seconds < 10:
            return f"00:0{time_seconds}"
        elif time_seconds < 60:
            return f"00:{time_seconds}"
        else:
            time_minutes = int(time_seconds / 60)
            if time_minutes < 10:
                minutes_string = f"0{time_minutes}"
            else:
                minutes_string = f"{time_minutes}"
            left_over_seconds = int(time_seconds - time_minutes * 60)
            if left_over_seconds < 10:
                seconds_string = f"0{left_over_seconds}"
            else:
                seconds_string = f"{left_over_seconds}"
            return f"{minutes_string}:{seconds_string}"

    def update(self) -> None:
        delta_time = World.get_delta_time()
        prev_time = self._time
        self._time += delta_time
        if prev_time != self._time:
            self.time_label.text = self.get_formatted_time()


class LevelState:
    """
    Singleton state data needed for the game to run.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls.boundary = Rect2(0, 0, 0, GameProperties().game_resolution.h)
            cls.floor_y = 78.0
            cls.is_paused = False
            cls.is_gate_transition_queued = False
            cls.is_currently_transitioning_within_level = False
            cls.is_paused_from_boss = False
            cls.screen_shader_instance: Optional[ShaderInstance] = None
            cls.bridge_gate_helper = BridgeGateHelper()
            cls.game_timer: Optional[GameTimer] = None
        return cls._instance

    def is_game_state_paused(self) -> bool:
        return (
            self.is_paused
            or self.is_currently_transitioning_within_level
            or self.is_paused_from_boss
        )

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance = None

    @staticmethod
    def queue_gate_transition() -> None:
        level_state = LevelState()
        level_state.is_gate_transition_queued = True
        level_state.is_currently_transitioning_within_level = True

    @staticmethod
    async def fade_transition(time: float, fade_out=True):
        try:
            level_state = LevelState()
            if fade_out:
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.75)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.5)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.25)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.0)
            else:
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.25)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.5)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 0.75)
                await co_suspend()
                level_state.screen_shader_instance.set_float_param("brightness", 1.0)
        except GeneratorExit:
            pass
