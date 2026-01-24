import asyncio
import logging
import coloredlogs
from enum import Enum
from pathlib import Path
from shepherdx.common import Config, Channels, Mode, Zone
from shepherdx.common.mqtt import ShepherdMqtt, ControlMessage, ControlMessageType

SHEPHERD_RUN_SERVICE_ID = "shepherd-run"

class State(str, Enum):
    INIT = "init"
    READY = "ready"
    RUNNING = "running"
    POST_RUN = "stopped"

class ShepherdRunner:
    def __init__(self):
        self.logger = logging.getLogger(SHEPHERD_RUN_SERVICE_ID)
        coloredlogs.install(level="DEBUG", logger=self.logger)

        self._state = State.INIT
        self._state_queue = asyncio.Queue()

        self._config = Config()
        self._set_defaults()

        self._usercode = None

    def run(self):
        asyncio.run(self._run_loop())

    def _reset_state(self):
        self._mode = Mode.DEV
        self._zone = Zone.RED

    async def _switch_state(self, new_state, old_state):
        """ Switch to new_state from old_state, checking old_state first """
        if self._state != old_state:
            self.logger.warn(f"Cannot switch to {new_state}, needs {old_state}, got {self._state}")
            return

        self.logger.info(f"Switching to {new_state}")
        await self._state_queue.put(new_state)

    async def _handle_control(self, msg: ControlMessage):
        if msg.type == ControlMessageType.START:
            self._mode = msg.mode
            self._zone = msg.zone
            await self._switch_state(State.RUNNING, State.READY)
        elif msg.type == ControlMessageType.STOP:
            await self._switch_state(State.POST_RUN, State.RUNNING)
        else:
            self.logger.warn(f"Unknown control message type: {msg.type}")

    async def _run_loop(self):
        async with ShepherdMqtt(SHEPHERD_RUN_SERVICE_ID) as mqttc:
            self._mqttc = mqttc
            await mqttc.subscribe(Channels.shepherd_run_control, self._handle_control, ControlMessage)

            try:
                await self._dispatch_state()
            except asyncio.exceptions.CancelledError:
                pass

    async def _dispatch_state(self):
        while True:
            if self._state == State.INIT:
                await self._state_init()
            elif self._state == State.READY:
                self._state_ready()
            elif self._state == State.RUNNING:
                self._state_running()
            elif self._state == State.POST_RUN:
                await self._state_post_run()

            # This blocks until the next state update is received
            self._state = await self._state_queue.get()

    async def _state_init(self):
        self.logger.info("INIT")
        await self._load_start_graphic()
        await self._state_queue.put(State.READY)

    def _state_ready(self):
        self.logger.info("READY")

    def _state_running(self):
        self.logger.info("RUNNING")

    async def _state_post_run(self):
        """ Move usercode back into ready state after running """
        self.logger.info("POST_RUN")
        self._reset_state()
        await self._state_queue.put(State.READY)

    async def _load_start_graphic(self):
        tmp_graphic = self._config.tmp_graphic
        start_graphic = self._config.team_logo_path
        if not start_graphic.exists():
            start_graphic = self._config.game_logo_path
        if not start_graphic.exists():
            self.logger.warn(f"No start graphic found, not creating {tmp_graphic}")

        content = start_graphic.read_bytes()
        tmp_graphic.write_bytes(content)

