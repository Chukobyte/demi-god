class LevelAreaType:
    NORMAL = "normal"
    POWER_UP = "power_up"
    BOSS = "boss"


class LevelArea:
    def __init__(self, width: int):
        self.width = width


class LevelAreaManager:
    def setup_level_area(self, area: LevelArea) -> None:
        pass
