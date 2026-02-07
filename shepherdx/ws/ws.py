import asyncio
from websockets import serve
from shepherdx.common.mqtt import ShepherdMqtt

SHEPHERD_WS_SERVICE_ID = "shepherd-ws"

class ShepherdWebSockets:
    def __init__(self):
        self._conns = []

    def run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        stop = asyncio.get_running_loop().create_future()

        async with serve(self._conn_handler, "0.0.0.0", 5001) as server:
            async with ShepherdMqtt(SHEPHERD_WS_SERVICE_ID) as mqttc:
                await mqttc.subscribe("#", self._mqtt_callback, None)

                try:
                    await stop  # This just runs the loops forever
                except asyncio.CancelledError:
                    pass

    async def _mqtt_callback(self, topic, payload):
        print(f"TOPIC: {topic}, MESSAGE: {payload}")

    async def _conn_handler(self, websocket):
        path = websocket.request.path[1::]
        print(f"CHANNEL: {path}")

