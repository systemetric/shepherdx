import shutil
import zipfile

from pathlib import Path
from fastapi import UploadFile
from PIL import Image

from shepherdx.common.config import Config

class Upload:
    def __init__(self):
        self._config = Config()

    async def _process_python(self, target_path: Path, f: UploadFile):
        content = await f.read()
        out_path = self._config.user_src_path / target_path

        with open(out_path, "wb") as f:
            f.write(content)

        shutil.copyfile(out_path, self._config.user_main_path)

    def _process_zip(self, path: Path, f: UploadFile) :
        pass

    async def upload_file(self, name: str, f: UploadFile):
        if f.content_type.startswith("text") or name.endswith(".py"):
            await self._process_python(Path(name), f)
        elif "zip" in f.content_type and zipfile.is_zipfile(f.file):
            self._process_zip(Path(name), f)
        else:
            raise Exception(f"File {f.filename} -> {name} has invalid MIME type {f.content_type}, or invalid ZIP file")

    def _process_image(self, f: UploadFile):
        img = Image.open(f.file)

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.save(self._config.team_logo_path)

    def upload_team_image(self, f: UploadFile):
        self._process_image(f)

