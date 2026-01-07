from pathlib import Path
from fastapi import UploadFile

from shepherdx.common.config import Config

class Upload:
    def __init__(self):
        self._config = Config()

    def upload_file(name: Path, f: UploadFile):
        pass

    def upload_team_image(f: UploadFile):
        pass

