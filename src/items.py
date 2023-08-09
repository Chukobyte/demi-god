from typing import Type

from crescent_api import *

from src.characters.player_stats import PlayerStats


class Item(Node2D):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.sprite: Optional[Sprite] = None
        self.collider: Optional[Collider2D] = None
        self.description: Optional[str] = None
        self._description_split: Optional[List[str]] = None
        self.can_be_collected = True
        self.play_collected_sfx = True
        self.active = False
        self.is_unique = False

    def _default_initialize(self, sprite_texture_path: str, size: Size2D) -> None:
        """
        Default initialization for all item objects.  If not used will need to manually create sprite and
        collider attached to the item.
        """
        self.sprite = Sprite.new()

        # Sprite
        self.sprite.texture = Texture(sprite_texture_path)
        self.sprite.draw_source = Rect2(0, 0, size.w, size.h)
        self.add_child(self.sprite)
        # Collider
        self.collider = Collider2D.new()
        self.collider.extents = size
        self.add_child(self.collider)

        # Item outline
        self.sprite.shader_instance = ShaderUtil.compile_shader(
            "shaders/outline.shader"
        )
        outline_color = Vector4(163.0 / 255.0, 163.0 / 255.0, 163.0 / 255.0, 1.0)
        self.sprite.shader_instance.set_float4_param("outline_color", outline_color)

        self._description_split = self._split_description_text()

    def _split_description_text(self, characters_per_line=19) -> List[str]:
        """
        Splits the item description text.  Max line is 19 characters long, for a total max of 38 characters.
        """
        if not self.description:
            return ["", ""]

        # Early out if less than 19 characters
        if len(self.description) <= characters_per_line:
            return [self.description, ""]

        lines = []
        current_line = ""
        words = self.description.split()
        for word in words:
            if len(current_line + " " + word) > characters_per_line:
                lines.append(current_line.strip())
                current_line = word
            else:
                current_line += " " + word

        # Add last line to the array
        lines.append(current_line.strip())

        return lines

    def set_item_highlighted(self, is_highlighted: bool) -> None:
        if is_highlighted:
            outline_width = 0.8
        else:
            outline_width = 0.0
        self.sprite.shader_instance.set_float_param("outline_width", outline_width)

    def on_activation(self) -> None:
        self.active = True

        lever_pull_audio_source = AudioManager.get_audio_source(
            path="assets/audio/sfx/lever_pull_item.wav"
        )
        AudioManager.play_sound(lever_pull_audio_source)

        self.broadcast_event("activated", self)

    def can_be_activated(self, stats: PlayerStats) -> bool:
        return not self.active

    def collect(self) -> None:
        self.broadcast_event("collected", self)
        self.queue_deletion()

    @property
    def description_top(self) -> str:
        if len(self._description_split) == 0:
            return ""
        return self._description_split[0]

    @property
    def description_bottom(self) -> str:
        if len(self._description_split) <= 1:
            return ""
        return self._description_split[1]


class ScrollItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Help the souls!"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_scroll.png",
            size=Size2D(12, 12),
        )
        self.position += Vector2(40, 0)


class LeverItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.can_be_collected = False

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_lever.png",
            size=Size2D(14, 14),
        )
        self.position += Vector2(40, -1)

    def on_activation(self) -> None:
        super().on_activation()
        self.sprite.flip_h = True


class HealthRestoreItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Restores health"
        self.restore_amount = 5

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_heart.png",
            size=Size2D(12, 12),
        )

    def can_be_activated(self, stats: PlayerStats) -> bool:
        return super().can_be_activated(stats) and stats and stats.hp < stats.base_hp


class EnergyRestoredFromAttacksIncreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Increase energy from attacks"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_energy_restored_from_attacks_increase.png",
            size=Size2D(12, 12),
        )


class DamageDecreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Reduces damage taken"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_damage_decrease.png",
            size=Size2D(12, 12),
        )


class SpecialAttackDoubledItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Chance to double special attack"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_special_attack_double.png",
            size=Size2D(12, 12),
        )


class SpecialAttackTimeDecreaseItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Decrease special attack charge time"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_special_attack_time_decrease.png",
            size=Size2D(12, 12),
        )


class SaveChargeItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Increase keep charge chance"

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_save_charge.png",
            size=Size2D(12, 12),
        )


class DamageDeflectWhenChargedItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Will deflect damage when charged"
        self.is_unique = True

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_damage_deflect_when_charged.png",
            size=Size2D(12, 12),
        )


class AbilitySlowTimeItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Will slow down time"
        self.is_unique = True

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_slow_time.png",
            size=Size2D(12, 12),
        )


class AbilityDualSpecialItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Will spawn projectiles"
        self.is_unique = True

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_dual_special.png",
            size=Size2D(12, 12),
        )


class AbilityHoodFormItem(Item):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.description = "Won't take hp damage when active"
        self.is_unique = True

    def _start(self):
        self._default_initialize(
            sprite_texture_path="assets/images/items/item_hood_form.png",
            size=Size2D(12, 12),
        )


class ItemUtils:
    @staticmethod
    def get_item_from_type(
        item_type: Type,
    ) -> HealthRestoreItem | ScrollItem | LeverItem | EnergyRestoredFromAttacksIncreaseItem | DamageDecreaseItem | SpecialAttackDoubledItem | SpecialAttackTimeDecreaseItem | SaveChargeItem | DamageDeflectWhenChargedItem | AbilitySlowTimeItem | AbilityDualSpecialItem | AbilityHoodFormItem | None:
        if issubclass(item_type, HealthRestoreItem):
            return HealthRestoreItem.new()
        elif issubclass(item_type, ScrollItem):
            return ScrollItem.new()
        elif issubclass(item_type, LeverItem):
            return LeverItem.new()
        elif issubclass(item_type, EnergyRestoredFromAttacksIncreaseItem):
            return EnergyRestoredFromAttacksIncreaseItem.new()
        elif issubclass(item_type, DamageDecreaseItem):
            return DamageDecreaseItem.new()
        elif issubclass(item_type, SpecialAttackDoubledItem):
            return SpecialAttackDoubledItem.new()
        elif issubclass(item_type, SpecialAttackTimeDecreaseItem):
            return SpecialAttackTimeDecreaseItem.new()
        elif issubclass(item_type, SaveChargeItem):
            return SaveChargeItem.new()
        elif issubclass(item_type, DamageDeflectWhenChargedItem):
            return DamageDeflectWhenChargedItem.new()
        elif issubclass(item_type, AbilitySlowTimeItem):
            return AbilitySlowTimeItem.new()
        elif issubclass(item_type, AbilityDualSpecialItem):
            return AbilityDualSpecialItem.new()
        elif issubclass(item_type, AbilityHoodFormItem):
            return AbilityHoodFormItem.new()
        print("ERROR: doesn't have item type in 'ItemUtils.get_item_from_type'!")
        return None

    @staticmethod
    def get_power_up_area_item_types() -> List[Type]:
        return [
            EnergyRestoredFromAttacksIncreaseItem,
            DamageDecreaseItem,
            SpecialAttackDoubledItem,
            SpecialAttackTimeDecreaseItem,
            SaveChargeItem,
            DamageDeflectWhenChargedItem,
        ]
