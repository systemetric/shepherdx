import asyncio
import coloredlogs, logging
from enum import Enum
from shepherdx.common import Channels, Mode, Zone
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

        self._mode = Mode.DEV
        self._zone = Zone.RED

    def run(self):
        asyncio.run(self._run_loop())

    # Switch state to `new_state` from `old_state`
    def _switch_state(self, new_state, old_state):
        if self._state != old_state:
            self.logger.warn(f"Cannot switch to {new_state}, needs {old_state}, got {self._state}")
            return

        self.logger.info(f"Switching to {new_state}")
        self._state_queue.put(new_state)

    async def _handle_control(self, msg: ControlMessage):
        if msg.type == ControlMessageType.START:
            self._mode = msg.mode
            self._zone = msg.zone
            self._switch_state(State.RUNNING, State.READY)
        elif msg.type == ControlMessageType.STOP:
            self._switch_state(State.POST_RUN, State.RUNNING)
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
                self._state_init()
            elif self._state == State.READY:
                self._state_ready()
            elif self._state == State.RUNNING:
                self._state_running()
            elif self._state == State.POST_RUN:
                self._state_post_run()

            # This blocks until the next state update is received
            self._state = await self._state_queue.get()

    def _state_init(self):
        self.logger.info("INIT")

    def _state_ready(self):
        self.logger.info("READY")

    def _state_running(self):
        self.logger.info("RUNNING")

    def _state_post_run(self):
        self.logger.info("POST_RUN")

