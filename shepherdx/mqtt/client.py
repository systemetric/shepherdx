import asyncio
import json

from aiomqtt import Client, Will
from dataclasses import asdict
from typing import Type, Callable
from .messages import MqttMessage

class MqttClient:
    def __init__(self, service, will = ""):
        self._mqttc = Client("localhost", will=Will(topic=f"{service}/status", payload=will))
        self._subs = {}
        asyncio.create_task(self._loop())

    async def __aenter__(self):
        await self._mqttc.__aenter__()
        return self

    async def __aexit__(self, type, val, db):
        await self._mqttc.__aexit__(type, val, db)
        return False

    async def _loop(self):
        async for msg in self._mqttc.messages:
            topic = msg.topic.value
            payload = json.loads(msg.payload.decode())
            if topic in self._subs:
                callback, cls = self._subs[topic]
                await callback(cls(**payload))

    async def subscribe(self, topic: str, callback: Callable[[MqttMessage], asyncio.Future], msg_type: Type[MqttMessage]):
        self._subs[topic] = (callback, msg_type)
        await self._mqttc.subscribe(topic)

    async def publish(self, topic: str, message: MqttMessage):
        await self._mqttc.publish(topic, json.dumps(asdict(message)).encode())

