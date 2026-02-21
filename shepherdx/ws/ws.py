import os
import json
import atexit
import base64
import asyncio
import logging
import threading
import websockets
import coloredlogs
from websockets import serve
from shepherdx.common import Config, Channels, State
from shepherdx.common.mqtt import ShepherdMqtt
from hopper import HopperPipe, HopperPipeType

BUF_SIZE = 65536
SHEPHERD_WS_SERVICE_ID = "shepherd-ws"

class ShepherdWebSockets:
    def __init__(self):
        self.logger = logging.getLogger(SHEPHERD_WS_SERVICE_ID)
        coloredlogs.install(level="DEBUG", logger=self.logger)

        self._conns = {}
        self._config = Config()

        if os.path.exists(self._config.tmp_graphic):
            with open(self._config.tmp_graphic, "rb") as f:
                fb = f.read()
                self._current_image = base64.b64encode(fb).decode() + "\n";
        else:
            self._current_image = None
        self._next_image = None
        self._camera_pipe = None
        self._logs = ""

    def run(self):
        self.logger.info("Starting Shepherd WS server")

        atexit.register(self._at_exit)

        self._camera_pipe = HopperPipe(HopperPipeType.OUT, SHEPHERD_WS_SERVICE_ID,
            Channels.camera, hopper=self._config.hopper_path)
        self._camera_pipe.open()

        self._image_thread = threading.Thread(target=self._load_images)
        self._image_thread.daemon = True
        self._image_thread.start()

        asyncio.run(self._loop())

    def _load_images(self):
        """ forever load images from hopper pipe into image buffer """
        image_buf = ""

        while True:
            buf = self._camera_pipe.read(BUF_SIZE).decode()
            buf = buf.split("\n")   # full images terminated with newlines

            for i in range(len(buf)):
                image_buf += buf[i]

                # last segment is always stored, not returned
                if i != len(buf) - 1:
                    self._next_image = image_buf
                    image_buf = ""

    def _at_exit(self):
        if self._camera_pipe:
            self._camera_pipe.close()

    async def _load_next_image(self):
        while self._next_image is None:
            await asyncio.sleep(1)

        # this is a race, but not a problematic one since valid data
        # is still guaranteed
        self._current_image = self._next_image
        self._next_image = None

    async def _loop(self):
        async with serve(self._conn_handler, "0.0.0.0", 5001) as server:
            async with ShepherdMqtt(SHEPHERD_WS_SERVICE_ID) as mqttc:
                await mqttc.subscribe("#", self._mqtt_callback, None)

                # forever broadcast new images from hopper
                while True:
                    await self._load_next_image()
                    ws = self._collect_ws(Channels.camera)
                    websockets.broadcast(ws, self._current_image)

    async def _mqtt_callback(self, topic, payload):
        if topic == Channels.shepherd_run_status:
            msg = json.loads(payload.decode())
            if str(msg["new_status"]) == State.POST_RUN.value:
                self._logs = ""
                self.logger.info("Cleared log buffer")
        if topic == Channels.robot_log:
            self._logs += payload.decode()

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

    async def _add_websocket(self, topic, websocket):
        if topic not in self._conns:
            self._conns[topic] = list([])

        self._conns[topic].append((websocket.id, websocket))
        self.logger.info(f"Added {websocket.id} for {topic}")

        if topic == Channels.camera and self._current_image is not None:
            await websocket.send(self._current_image)
            self.logger.info(f"Sent image to {websocket.id}")
        elif topic == Channels.robot_log:
            await websocket.send(self._logs)
            self.logger.info(f"Sent logs to {websocket.id}")

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
        await self._add_websocket(path, websocket)

        try:
            await websocket.wait_closed()
        finally:
            self._remove_websocket(path, websocket)

