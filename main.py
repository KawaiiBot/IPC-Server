import asyncio
import traceback
import json


clients = {}
loop = asyncio.get_event_loop()
results = []


def encode(data: dict) -> str:
    a = json.dumps(data) + '\n'
    return a.encode()

async def timeout(time: int):
    await asyncio.sleep(time)
    unused_futures = [f for f in results if not f.done()]
    for future in unused_futures:
        future.set_result(None)


class Client:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    print('Client Connected!')
    loop.create_task(listen(reader, writer))


async def listen(reader, writer):
    while True:
        try:
            data = await reader.readline()
            await handle_data(data, reader, writer)
        except Exception as e:
            print('An unknown error occurred while listening for data')
            print(e)


async def handle_data(data, reader, writer) -> None:
    try:
        data = json.loads(data.decode())

        if not data['op']:
            return

        if data['op'] == 'LINK':
            i = data['d']['id']
            clients.update({
                i: Client(reader, writer)
            })
            print(f'[IPC] Linked instance {i}')
        elif data['op'] == 'EXEC':
            for client in clients:
                if data['id'] != client:
                    results.append(asyncio.Future())
                    w = clients[client].writer
                    d = {
                        'op': 'RUN',
                        'd': data['d']
                    }
                    w.write(encode(d))
                    await w.drain()

            _timeout = loop.create_task(timeout(15))  # 15 second timeout 

            r = {
                'op': 'RESULTS',
                'd': await asyncio.gather(*results)
            }

            if not _timeout.done():
                _timeout.cancel()

            writer.write(encode(r))
            results.clear()
        elif data['op'] == 'RESULT':
            unused_futures = [f for f in results if not f.done()]
            unused_futures[0].set_result(data['d'])
        else:
            pass
    except Exception:
        traceback.print_exc()
    else:
        await writer.drain()


if __name__ == '__main__':
    server = loop.run_until_complete(asyncio.start_server(client_connected, '127.0.0.1', 420, loop=loop))
    print('[IPC] Listening...')

    loop.run_forever()
