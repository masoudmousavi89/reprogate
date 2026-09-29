import trio
import trio_websocket
from trio_websocket import serve_websocket, open_websocket_url

async def handler(request):
    await request.accept()

async def main():
    async with trio.open_nursery() as nursery:
        server = await nursery.start(serve_websocket, handler, '127.0.0.1', 0, None)
        port = server.port
        # URL without a path component
        async with open_websocket_url('ws://127.0.0.1:%d' % port) as ws:
            pass
        nursery.cancel_scope.cancel()

trio.run(main)
