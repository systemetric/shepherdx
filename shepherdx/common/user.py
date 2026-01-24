import dataclasses

from enum import Enum
from dataclasses import dataclass, fields
from typing import Optional

class Zone(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"

class Mode(str, Enum):
    DEV = "dev"
    COMP = "comp"

@dataclass
class UserConfig:
    zone: Zone = Zone.RED
    mode: Mode = Mode.DEV

    def __post_init__(self):
        # https://stackoverflow.com/a/69944614
        for field in fields(self):
            if not isinstance(field.default, dataclasses._MISSING_TYPE) and getattr(self, field.name) is None:
                setattr(self, field.name, field.default)

        if self.zone not in list(Zone):
            raise ValueError(f"zone '{self.zone}' not valid")
        if self.mode not in list(Mode):
            raise ValueError(f"mode '{self.mode}' not valid")

class State(str, Enum):
    INIT = "init"
    READY = "ready"
    RUNNING = "running"
    POST_RUN = "stopped"

