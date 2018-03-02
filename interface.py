import asyncio
import json


class ConnectionCog:
    def __init__(self, ID: str, bot):
        loop = bot.loop
        self.id: str = ID
        self.bot = bot
        self.reader, self.writer = loop.run_until_complete(asyncio.open_connection("127.0.0.1", 420))
        self._task = loop.create_task(self.setup_ipc(self.reader, self.writer))

        self.pending_result = None

    async def send(self, data: dict, expect_result=False) -> None:
        if expect_result:
            self.pending_result = asyncio.Future()

        data = (json.dumps(data) + '\n').encode()
        self.writer.write(data)
        await self.writer.drain()

        if expect_result:
            await self.pending_result
            return self.pending_result.result()

    async def setup_ipc(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await self.link(reader, writer)
        while True:
            data = json.loads((await reader.readline()).decode())

            if not data['op']:
                return

            if data['op'] == 'RUN':
                if data['d']['command'] == 'eval':
                    resp = {
                        'op': 'RESULT',
                        'd': self._eval(data['d']['args']),
                        'id': self.bot.instance
                    }
                    await self.send(resp)

                elif data['d']['command'] == 'reload':
                    resp = {
                        'op': 'RESULT',
                        'd': self._reload_cog(data['d']['args']),
                        'id': self.bot.instance
                    }
                    await self.send(resp)

            elif data['op'] == 'RESULTS':
                if self.pending_result:
                    self.pending_result.set_result(data['d'])

    async def link(self, reader, writer):
        _link = {
            'op': 'LINK',
            'd': {
                'id': self.id
            }
        }
        await self.send(_link)

    # IPC Commands
    def _eval(self, args):
        env = {
            'bot': self.bot
        }

        try:
            return eval(args, env)
        except Exception:
            return None

    def _reload_cog(self, cog):
        self.bot.unload_extension(f'cogs.{cog}')
        try:
            self.bot.load_extension(f'cogs.{cog}')
            return True
        except Exception:
            return False
