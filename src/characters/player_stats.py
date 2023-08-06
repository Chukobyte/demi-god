from typing import Optional

from crescent_api import Size2D, ColorRect, SceneTree

from src.utils.game_math import clamp, map_to_range


class PlayerStats:
    def __init__(
        self,
        base_hp=0.0,
        base_energy=0.0,
        base_move_speed=0,
        base_energy_restored_from_attacks=0.0,
        special_attack_charge_time=0.0,
    ):
        self._hp = base_hp
        self._base_hp = base_hp
        self._energy = base_energy
        self._base_energy = base_energy
        self._move_speed = base_move_speed
        self._base_move_speed = base_move_speed
        self._energy_restored_from_attacks = base_energy_restored_from_attacks
        self._base_energy_restored_from_attacks = base_energy_restored_from_attacks
        self.special_attack_charge_time = special_attack_charge_time
        self.save_charge_chance = 0
        self.double_special_attack_chance = 0
        self.health_bar_ui: Optional[ColorRect] = None
        self.energy_bar_ui: Optional[ColorRect] = None
        self.base_health_bar_ui_size = Size2D(52, 9)
        self.base_energy_bar_ui_size = Size2D(52, 9)
        # Stats that will only be touched by items
        self.transformation_energy_drain = 1
        self.damage_taken_from_attacks_multiple = 1.0

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

    @property
    def move_speed(self) -> int:
        return self._move_speed

    @move_speed.setter
    def move_speed(self, value: int) -> None:
        self._move_speed = value

    @property
    def energy_restored_from_attacks(self) -> float:
        return self._energy_restored_from_attacks

    @energy_restored_from_attacks.setter
    def energy_restored_from_attacks(self, value: float) -> None:
        self._energy_restored_from_attacks = value

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

    def reset_move_speed(self) -> None:
        self._move_speed = self._base_move_speed

    def reset_energy_restored_from_attacks(self) -> None:
        self._energy_restored_from_attacks = self._base_energy_restored_from_attacks
