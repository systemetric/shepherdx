from shepherdx.common import Config, UserConfig, Channels, Zone, Mode
from shepherdx.common.mqtt import ControlMessage, ControlMessageType

class Control:
    def __init__(self):
        self._config = Config()
        self._user_config = UserConfig(zone=Zone.RED, mode=Mode.DEV)

    def set_user_config(self, config: UserConfig):
        self._user_config = config

    async def start_user(self, mqttc):
        message = ControlMessage(
            type=ControlMessageType.START,
            zone=self._user_config.zone,
            mode=self._user_config.mode,
        )

        await mqttc.publish(Channels.shepherd_run_control, message)

    async def stop_user(self, mqttc):
        message = ControlMessage(
            type=ControlMessageType.STOP,
            zone=None,
            mode=None,
        )

        await mqttc.publish(Channels.shepherd_run_control, message)

