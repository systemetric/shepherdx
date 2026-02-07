# This file defines message subclasses for MQTT communication

from shepherdx.common.user import Mode, State

from dataclasses import dataclass
from enum import Enum

@dataclass
class MqttMessage:
    pass

class ControlMessageType(str, Enum):
    START = "start"
    STOP = "stop"

@dataclass
class ControlMessage(MqttMessage):
    type: ControlMessageType
    mode: Mode | None
    zone: int | None

@dataclass
class RunStatusMessage(MqttMessage):
    new_state: State

