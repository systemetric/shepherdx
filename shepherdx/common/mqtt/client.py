import asyncio
import aiomqtt
import json

from aiomqtt import Client, Will
from dataclasses import asdict
from typing import Type, Callable, Optional
from .messages import MqttMessage

class ShepherdMqtt:
    def __init__(self, service, will = ""):
        self._mqttc = Client("localhost", will=Will(topic=f"{service}/status", payload=will))
        self._subs = {}
        self._task = asyncio.create_task(self._loop_wrapper())

    async def __aenter__(self):
        await self._mqttc.__aenter__()
        return self

    async def __aexit__(self, type, val, db):
        await self._mqttc.__aexit__(type, val, db)
        return False

    async def _loop_wrapper(self):
        try:
            await self.loop()
        except aiomqtt.exceptions.MqttError as e:
            # If a better solution emerges to suppress this error, use it
            # Currently, this error has no code, just a message
            if str(e) == "Disconnected during message iteration":
                pass
            else:
                raise e

    async def loop(self):
        async for msg in self._mqttc.messages:
            topic = msg.topic.value
            if topic in self._subs:
                callback, cls = self._subs[topic]

                if cls == None:
                    await callback(msg.payload)
                else:
                    payload = json.loads(msg.payload.decode())
                    await callback(cls(**payload))

    async def subscribe(self, topic: str, callback: Callable[[MqttMessage], asyncio.Future], msg_type: Optional[Type[MqttMessage]]):
        self._subs[topic] = (callback, msg_type)
        await self._mqttc.subscribe(topic)

    async def publish(self, topic: str, message: MqttMessage):
        await self._mqttc.publish(topic, json.dumps(asdict(message)).encode())

