from fastapi import APIRouter, HTTPException, Response, Request, UploadFile
from pathlib import Path

from shepherdx.common import Config
from .editor import Editor
from .upload import Upload

class Router:
    def __init__(self):
        self._config = Config()
        self._editor = Editor()
        self._upload = Upload()

        self._files_router = APIRouter(prefix="/files")
        self._files_router.add_api_route("/list", self.get_files, methods=["GET"])
        self._files_router.add_api_route("/load/{filename}", self.load_file, methods=["GET"])
        self._files_router.add_api_route("/save/{filename}", self.save_file, methods=["POST"])
        self._files_router.add_api_route("/delete/{filename}", self.delete_file, methods=["POST"])

        self._upload_router = APIRouter(prefix="/upload")
        self._upload_router.add_api_route("/file", self.upload_file, methods=["POST"], status_code=201)
        self._upload_router.add_api_route("/team-image", self.upload_team_image, methods=["POST"], status_code=201)

    @property
    def files_router(self):
        return self._files_router

    @property
    def upload_router(self):
        return self._upload_router

    async def get_files(self):
        return await self._editor.get_files()

    async def load_file(self, filename: str):
        try:
            return await self._editor.load_file(Path(filename))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load {filename}: {e}")

    async def save_file(self, filename: str, request: Request):
        try:
            await self._editor.save_file(Path(filename), (await request.body()).decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {filename}: {e}")

    async def delete_file(self, filename: str):
        try:
            await self._editor.delete_file(Path(filename))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {e}")

    async def upload_file(self, f: UploadFile):
        try:
           await self._upload.upload_file(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload: {e}")

    async def upload_team_image(self, f: UploadFile):
        try:
            self._upload.upload_team_image(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload team image: {e}")

