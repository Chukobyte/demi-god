from typing import Optional, List

from crescent_api import Rect2, ShaderInstance, Vector2, SceneTree

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

    def get_next_bridge_gate(self) -> BridgeGate:
        self._current_gate_index += 1
        if self._current_gate_index > self.max_bridges - 1:
            self._current_gate_index = 0
        return self._bridge_gates[self._current_gate_index]

    def open_gates(self) -> None:
        for gate in self._bridge_gates:
            gate.set_opened()

    def close_gates(self) -> None:
        for gate in self._bridge_gates:
            gate.set_closed()


class LevelState:
    """
    Singleton state data needed for the game to run.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls.boundary = Rect2(0, 0, 0, 144)
            cls.floor_y = 78.0
            cls.is_paused = False
            cls.is_gate_transition_queued = False
            cls.is_currently_transitioning_within_level = False
            cls.screen_shader_instance: Optional[ShaderInstance] = None
            cls.bridge_gate_helper = BridgeGateHelper()
        return cls._instance

    def is_game_state_paused(self) -> bool:
        return self.is_paused or self.is_currently_transitioning_within_level

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
