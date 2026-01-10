# This file defines message subclasses for MQTT communication

from dataclasses import dataclass

@dataclass
class MqttMessage:
    pass

@dataclass
class CountMessage(MqttMessage):
    num: int
