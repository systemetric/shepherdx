import asyncio
import json

from aiomqtt import Client
from dataclasses import asdict
from typing import Type, Callable
from .messages import MqttMessage

class MqttClient:
    def __init__(self, will = ""):
        self._mqttc = Client("localhost", will=will)
        self._subs = {}

    async def run(self):
        asyncio.create_task(self._loop())

    async def _loop(self):
        async for msg in self._mqttc.messages:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            if topic in self._subs:
                callback, cls = self._subs[topic]
                await self._subs[topic](cls(**payload))

    async def subscribe(self, topic: str, callback: Callable[[MqttMessage], asyncio.Future], msg_type: Type[MqttMessage]):
        self._subs[topic] = (callback, msg_type)
        await self._mqttc.subscribe(topic)

    async def publish(self, topic: str, message: MqttMessage):
        await self._mqttc.publish(topic, json.dumps(asdict(Message)).encode())

