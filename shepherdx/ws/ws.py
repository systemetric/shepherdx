import asyncio
from websockets import serve

class ShepherdWebSockets:
    def __init__(self):
        self._conns = []

    def run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        stop = asyncio.get_running_loop().create_future()
        async with serve(self._conn_handler, "0.0.0.0", 5001) as server:
            await stop

    async def _conn_handler(self, websocket):
        path = websocket.request.path[1::]
        print(f"Channel: {path}")

