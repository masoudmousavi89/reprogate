from functools import partial

import trio
import trio_websocket


async def idle_server(stream):
    async with stream:
        await trio.sleep(5)


async def main():
    async with trio.open_nursery() as nursery:
        listeners = await nursery.start(partial(trio.serve_tcp, idle_server, 0, host="127.0.0.1"))
        port = listeners[0].socket.getsockname()[1]
        # URL without a path component, as in the report (local server instead of wss://ws.kraken.com)
        async with trio_websocket.open_websocket_url("ws://127.0.0.1:%d" % port):
            pass
        nursery.cancel_scope.cancel()

trio.run(main)
