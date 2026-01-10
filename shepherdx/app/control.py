from shepherdx.common import Config, UserConfig

class Control:
    def __init__(self):
        self._config = Config()
        self._user_config = UserConfig.default()

    def start_user(self):
        pass

    def stop_user(self):
        pass

    

