import os
import json

from pathlib import Path

from shepherdx.common import Config

class Editor:
    def __init__(self):
        self._config = Config()

    def _get_blocks(self) -> dict:
        blocks = {}
        if self._config.blocks_path.exists():
            with open(self._config.blocks_path, "r") as f:
                try:
                    blocks = json.load(f)
                except ValueError:
                    pass

        if "requires" not in blocks:
            blocks["requires"] = []
        if "header" not in blocks:
            blocks["header"] = ""
        if "footer" not in blocks:
            blocks["footer"] = ""
        if "blocks" not in blocks:
            blocks["blocks"] = []

        return blocks

    def _get_projects(self) -> list:
        project_paths = [f for f in os.listdir(self._config.user_src_path)
                         if os.path.isfile(os.path.join(self._config.user_src_path, f))
                         and (f.endswith(".py") or f.endswith(".xml") or f == "blocks.json")
                         and f != "main.py"]

        return project_paths

    async def get_files(self) -> dict:
        blocks = self._get_blocks()
        projects = self._get_projects()

        return {
            "blocks": blocks,
            "projects": projects,
        }

    async def load_file(self, name: Path) -> dict:
        path = self._config.user_src_path / name

        with open(path, "r") as f:
            content = f.read()

        return {
            "filename": name,
            "content": content,
        }

    async def save_file(self, name: Path, body: str):
        path = self._config.user_src_path / name

        with open(path, "w") as f:
            f.write(body)

    async def delete_file(self, name: Path):
        if name == "blocks.json":
            return

        path = self._config.user_src_path / name
        os.unlink(path)

