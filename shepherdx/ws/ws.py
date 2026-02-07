import asyncio
import logging
import websockets
import coloredlogs
from websockets import serve
from shepherdx.common import Config
from shepherdx.common.mqtt import ShepherdMqtt

SHEPHERD_WS_SERVICE_ID = "shepherd-ws"

class ShepherdWebSockets:
    def __init__(self):
        self.logger = logging.getLogger(SHEPHERD_WS_SERVICE_ID)
        coloredlogs.install(level="DEBUG", logger=self.logger)

        self._conns = {}
        self._config = Config()

    def run(self):
        self.logger.info("Started Shepherd WS server")
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
        if topic in self._conns.keys():
            ws = self._collect_ws(topic)
            websockets.broadcast(ws, payload)
            self.logger.info(f"{topic} <- {len(payload)} bytes")

    # collect websockets by topic for broadcast
    def _collect_ws(self, topic):
        if topic not in self._conns:
            return []

        final_ws = []
        for id, ws in self._conns[topic]:
            final_ws.append(ws)

        return final_ws

    def _add_websocket(self, topic, websocket):
        if topic not in self._conns:
            self._conns[topic] = list([])

        self._conns[topic].append((websocket.id, websocket))

        self.logger.info(f"Added {websocket.id} for {topic}")

    def _remove_websocket(self, topic, websocket):
        if topic not in self._conns:
            return

        removed = False

        # filter connections list, remove matching ids
        new_conns = []
        for id, ws in self._conns[topic]:
            if id == websocket.id:
                removed = True
            else:
                new_conns.append((id, ws))
        self._conns[topic] = new_conns

        if removed:
            self.logger.info(f"Removed {websocket.id} from {topic}")

    async def _conn_handler(self, websocket):
        path = websocket.request.path[1::]
        self._add_websocket(path, websocket)

        try:
            await websocket.wait_closed()
        finally:
            self._remove_websocket(path, websocket)

