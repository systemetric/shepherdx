import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shepherdx.common.config import Config

class ShepherdHttp:
    def __init__(self, host, port):
        self._config = Config()

        self._host = host
        self._port = port
        self._app = FastAPI()

        self._app.mount("/editor", StaticFiles(directory=self._config.editor_path, html=True), name="editor")
        self._app.mount("/docs", StaticFiles(directory=self._config.docs_path, html=True), name="docs")

    def run(self):
        uvicorn.run(self._app, port=self._port, host=self._host)

