import os
import shutil
import zipfile
import tempfile

from pathlib import Path
from fastapi import UploadFile
from PIL import Image

from shepherdx.common.config import Config

class Upload:
    def __init__(self):
        self._config = Config()

    async def _process_python(self, f: UploadFile):
        shutil.rmtree(self._config.user_cur_path, ignore_errors=True)
        os.makedirs(self._config.user_cur_path, exist_ok=True)

        content = await f.read()
        with open(self._config.user_main_path, "wb") as f:
            f.write(content)

    def _process_zip(self, f: UploadFile):
        tmp_dir = tempfile.mkdtemp(prefix="shepherd_user_code_")

        with zipfile.ZipFile(f.file, "r") as zip:
            zip.extractall(tmp_dir)

        if not (Path(tmp_dir) / self._config.user_main_name).is_file():
            raise Exception("Uploaded ZIP file has no entrypoint")

        shutil.rmtree(self._config.user_cur_path, ignore_errors=True)
        shutil.move(tmp_dir, self._config.user_cur_path)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    async def upload_file(self, f: UploadFile):
        if f.content_type.startswith("text") or f.filename.endswith(".py"):
            await self._process_python(f)
        elif "zip" in f.content_type and zipfile.is_zipfile(f.file):
            self._process_zip(f)
        else:
            raise Exception(f"File {f.filename} -> {name} has invalid MIME type {f.content_type}, or invalid ZIP file")

    def _process_image(self, f: UploadFile):
        img = Image.open(f.file)

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.save(self._config.team_logo_path)

    def upload_team_image(self, f: UploadFile):
        self._process_image(f)

