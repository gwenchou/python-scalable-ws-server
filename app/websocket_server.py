import os
import asyncio
import websockets
import aioredis


websocket_serve_host = '0.0.0.0'
websocket_serve_port = os.environ.get('WEBSOCKET_SERVE_PORT', 8000)
redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1?encoding=utf-8')

class WebsocketServer:
    def __init__(self):
        self.websocket_server = None
        self.redis_sub = None
        self.redis_pub = None

        self.clients = set()

    def main(self):
        asyncio.run(self.start_server())

    async def start_server(self):
        await self.init_redis_connection()
        self.websocket_server = await websockets.serve(
            ws_handler=self.entry_point,
            host=websocket_serve_host,
            port=websocket_serve_port
        )

        await self.subscribe('global-channel')

        print(f"Serve WebSocket server on ws://{websocket_serve_host}:{websocket_serve_port}")
        await self.websocket_server.wait_closed()

    async def init_redis_connection(self):
        self.redis_sub = await aioredis.create_redis(
            redis_url
        )
        self.redis_pub = await aioredis.create_redis(
            redis_url
        )

    async def entry_point(self, websocket, path):
        print(f"New Client connected: {id(websocket)}")
        try:
            self.register_client(websocket)

            await asyncio.create_task(self.websocket_message_reader(websocket))
        except Exception as e:
            print(e)
        finally:
            self.unregister_client(websocket)
            print(f"Connection closed: {id(websocket)}")

    async def websocket_message_reader(self, websocket):
        async for message in websocket:
            print(f"{id(websocket)}: {message}")

    async def redis_message_reader(self, channel):
        while (await channel.wait_message()):
            msg = await channel.get_json()
            print("Redis got message:", msg)

    async def subscribe(self, channel_name: str):
        channel, = await self.redis_sub.subscribe(channel_name)
        asyncio.create_task(self.redis_message_reader(channel))
        print(f"Subscribed redis pub/sub channel: {channel_name}")

    def register_client(self, websocket):
        self.clients.add(websocket)

    def unregister_client(self, websocket):
        self.clients.remove(websocket)
