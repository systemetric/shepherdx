import sys
import json
import errno
import atexit
import asyncio
import logging
import subprocess
import coloredlogs
from typing import Optional
from enum import Enum
from pathlib import Path
from shepherdx.common import (
    Config,
    Channels,
    Mode,
    Zone,
    State,
)
from shepherdx.common.mqtt import (
    ShepherdMqtt,
    ControlMessage,
    ControlMessageType,
    RunStatusMessage,
)

try:
    import RPi.GPIO as GPIO
except Exception:
    import Mock.GPIO as GPIO

SHEPHERD_RUN_SERVICE_ID = "shepherd-run"

class ShepherdRunner:
    def __init__(self):
        self.logger = logging.getLogger(SHEPHERD_RUN_SERVICE_ID)
        coloredlogs.install(level="DEBUG", logger=self.logger)

        self._state = State.INIT
        self._state_queue = asyncio.Queue()

        self._config = Config()
        self._reset_state()

        self._usercode = None
        self._user_wait_thread = None
        self._user_timer_thread = None

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

    def _switch_state_user_exit(self):
        """ Switch state into POST_RUN, ignore current state unless INIT """
        if self._state != State.INIT:
            self._state_queue.put_nowait(State.POST_RUN)
        else:
            self.logger.warn(f"Cannot switch to POST_RUN, needs > INIT, got {self._state}")

    async def _handle_control(self, topic: str, msg: ControlMessage):
        if msg.type == ControlMessageType.START:
            self._mode = msg.mode
            self._zone = msg.zone
            await self._switch_state(State.RUNNING, State.READY)
        elif msg.type == ControlMessageType.STOP:
            # transition to POST_RUN in READY or RUNNING state
            await self._switch_state(State.POST_RUN,
                self._state if self._state == State.READY or self._state == State.RUNNING else State.RUNNING)
        else:
            self.logger.warn(f"Unknown control message type: {msg.type}")

    def _gpio_start(self, _):
        zone = Zone.RED
        if (self._config.arena_usb_path / "zone1.txt").exists():
            zone = Zone.BLUE
        elif (self._config.arena_usb_path / "zone2.txt").exists():
            zone = Zone.GREEN
        elif (self._config.arena_usb_path / "zone3.txt").exists():
            zone = Zone.YELLOW

        self._mode = Mode.COMP
        self._zone = zone

        # this does block, but it shouldn't matter (also gpio is not async)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._switch_state(State.RUNNING, State.READY))

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._config.start_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self._config.start_button_pin, GPIO.FALLING,
            callback=self._gpio_start, bouncetime=self._config.start_button_bounce_time)

    def _at_exit(self):
        if self._user_wait_thread:
            self._user_wait_thread.cancel("")
        if self._user_timer_thread:
            self._user_timer_thread.cancel("")

        self._kill_usercode()

    def _send_start_info(self):
        """ Send start info down the start pipe, to waiting usercode """
        s = json.dumps({
            "mode": self._mode,
            "zone": self._zone,
        })
        self._start_pipe.write(s.encode("utf-8") + b'\n')

    def _wait_usercode(self, loop: asyncio.AbstractEventLoop, timeout: Optional[float]):
        """ Wait for usercode to exit, and safely transition to POST_RUN, optional timeout """
        if self._usercode == None:
            return

        try:
            self._usercode.wait(timeout)
        except subprocess.TimeoutExpired:
            pass

        if timeout:
            self.logger.debug(f"EXPIRE: {timeout}")
        loop.call_soon_threadsafe(self._switch_state_user_exit)

    def _set_usercode_timer(self):
        timeout = self._config.round_length if self._mode == Mode.COMP else None
        if timeout == None:
            return

        self.logger.debug(f"TIMEOUT: {timeout}")
        loop = asyncio.get_running_loop()
        self._user_timer_thread = asyncio.create_task(asyncio.to_thread(self._wait_usercode, loop, timeout))

    async def _start_usercode(self):
        self._usercode = subprocess.Popen(
            [
                sys.executable, "-u", self._config.user_main_path
            ],
            stdout = self._log_pipe.fd,
            stderr = self._log_pipe.fd,
            bufsize = 1,
            close_fds = True,
        )

        loop = asyncio.get_running_loop()
        self._user_wait_thread = asyncio.create_task(asyncio.to_thread(self._wait_usercode, loop, None))

    async def _stop_usercode(self):
        """ Stop the usercode, sending SIGKILL if needed """
        if self._usercode == None:
            return

        if self._user_wait_thread:
            self._user_wait_thread.cancel("")

        if self._user_timer_thread:
            self._user_timer_thread.cancel("")

        if self._state != State.RUNNING and self._state != State.POST_RUN:
            self.logger.warn(f"Cannot kill usercode, needs RUNNING or POST_RUN, got {self._state}")
            return

        try:
            self._usercode.terminate()
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise

        if self._usercode.poll() == None:
            await asyncio.sleep(self._config.kill_delay)
            self._kill_usercode()

        self._usercode = None
        self.logger.info("Killed usercode")

    def _kill_usercode(self):
        """ Kill usercode with SIGKILL """
        if self._usercode == None:
            return

        try:
            self._usercode.kill()
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise

    async def _run_loop(self):
        async with ShepherdMqtt(SHEPHERD_RUN_SERVICE_ID) as mqttc:
            self._mqttc = mqttc
            await mqttc.subscribe(Channels.shepherd_run_control, self._handle_control, ControlMessage)

            try:
                await self._dispatch_state()
            except asyncio.exceptions.CancelledError:
                pass

    async def _dispatch_state(self):
        """ Dispatch state transitions forever """
        while True:
            # publish new state on status channel, could be used to reset clients
            await self._mqttc.publish(Channels.shepherd_run_status, RunStatusMessage(new_state=self._state))

            if self._state == State.INIT:
                await self._state_init()
            elif self._state == State.READY:
                await self._state_ready()
            elif self._state == State.RUNNING:
                self._state_running()
            elif self._state == State.POST_RUN:
                await self._state_post_run()

            # This blocks until the next state update is received
            self._state = await self._state_queue.get()

    async def _state_init(self):
        """ Initialize the runner, this only happens once """
        self.logger.info("INIT")

        self._setup_gpio()
        self._setup_hopper()

        atexit.register(self._at_exit)

        await self._load_start_graphic()
        await self._state_queue.put(State.READY)

    async def _state_ready(self):
        """ Start the usercode, until it blocks for start info """
        self.logger.info("READY")
        await self._start_usercode()

    def _state_running(self):
        """ Send start info to usercode when transitioning """
        self.logger.info("RUNNING")
        self._send_start_info()
        self._set_usercode_timer()

    async def _state_post_run(self):
        """ Move usercode back into ready state after running """
        self.logger.info("POST_RUN")
        await self._stop_usercode()
        self._reset_state()
        await self._state_queue.put(State.READY)

    async def _load_start_graphic(self):
        """ Copy an image to the temporary initial image location """
        tmp_graphic = self._config.tmp_graphic
        start_graphic = self._config.team_logo_path
        if not start_graphic.exists():
            start_graphic = self._config.game_logo_path
        if not start_graphic.exists():
            self.logger.warn(f"No start graphic found, not creating {tmp_graphic}")

        content = start_graphic.read_bytes()
        tmp_graphic.write_bytes(content)

