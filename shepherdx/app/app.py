import uvicorn
import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shepherdx.common import Config
from shepherdx.common.mqtt import ShepherdMqtt

from .router import Router

SHEPHERD_SERVICE_ID = "shepherd-app";

class ShepherdApp:
    def __init__(self, host: str, port: int):
        self._config = Config()

        self._host = host
        self._port = port
        self._app = FastAPI(lifespan=self._init_mqtt, docs_url=None, redoc_url=None, openapi_url=None)
        self._router = Router(self.get_mqtt_client)

        self._app.mount("/editor", StaticFiles(directory=self._config.editor_path, html=True), name="editor")
        self._app.mount("/docs", StaticFiles(directory=self._config.docs_path, html=True), name="docs")
        self._app.mount("/", StaticFiles(directory=self._config.static_path, html=True), name="static")

        self._app.include_router(self._router.files_router)
        self._app.include_router(self._router.upload_router)
        self._app.include_router(self._router.control_router)

    async def _init_mqtt(self, app: FastAPI):
        async with ShepherdMqtt(SHEPHERD_SERVICE_ID) as client:
            self._mqtt_client = client
            yield

    async def get_mqtt_client(self):
        return self._mqtt_client

    def run(self):
        uvicorn.run(self._app, port=self._port, host=self._host)

