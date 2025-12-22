from fastapi import APIRouter, HTTPException, Request
from pathlib import Path

from shepherdx.common.config import Config
from .editor import Editor

class Router:
    def __init__(self):
        self._config = Config()
        self._editor = Editor()

        self._files = APIRouter(prefix="/files")
        self._files.add_api_route("/", self.get_files, methods=["GET"])
        self._files.add_api_route("/load/{filename}", self.load_file, methods=["GET"])
        self._files.add_api_route("/save/{filename}", self.save_file, methods=["POST"])
        self._files.add_api_route("/delete/{filename}", self.delete_file, methods=["POST"])

    @property
    def files_router(self):
        return self._files

    async def get_files(self):
        return self._editor.get_files()

    async def load_file(self, filename: str):
        name = Path(filename)

        try:
            return self._editor.load_file(name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load {filename}: {e}")

    async def save_file(self, filename: str, request: Request):
        name = Path(filename)

        try:
            self._editor.save_file(name, (await request.body()).decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {filename}: {e}")

    async def delete_file(self, filename: str):
        name = Path(filename)

        try:
            self._editor.delete_file(name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {e}")

