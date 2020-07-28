import asyncio
from websocket_server import WebsocketServer


server = WebsocketServer()
asyncio.run(server.start_server())
