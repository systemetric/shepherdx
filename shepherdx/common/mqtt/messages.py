# This file defines message subclasses for MQTT communication

from shepherdx.common.user import Zone, Mode

from dataclasses import dataclass
from enum import Enum

@dataclass
class MqttMessage:
    pass

@dataclass
class ControlMessageType(Enum):
    START = "start"
    STOP = "stop"

@dataclass
class ControlMessage:
    type: ControlMessageType
    mode: Mode | None
    zone: Zone | None

