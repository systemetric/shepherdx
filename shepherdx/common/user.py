from enum import Enum

class Zone(Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"

class Mode(Enum):
    DEV = "DEV"
    COMP = "COMP"

class UserConfig:
    def __init__(self, zone: Zone, mode: Mode):
        self._zone = zone
        self._mode = mode

    def default():
        return UserConfig(Zone.RED, Mode.DEV)

    @property
    def zone(self):
        return self._zone

    @property
    def mode(self):
        return self._mode

